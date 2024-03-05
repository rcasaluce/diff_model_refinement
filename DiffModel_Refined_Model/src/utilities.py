import argparse
import warnings
warnings.filterwarnings('ignore')
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.log.importer.xes import importer as xes_importer
from pm4py.objects.log.util import dataframe_utils
from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
from pm4py.objects.conversion.process_tree import converter as pt_converter
import pandas as pd
import pm4py
import numpy as np
import graphviz
import pylab
import pydotplus
import re
import pydot
import os
import pygraphviz as pgv
import copy


file_path_csv =  './data/csv/'
file_path_dot = './data/dot/'
file_path_results = './data/results_DIFF/'
file_path_bbt = './data/bbt/'



def load_csv_file(file): 
    
    """
    Load a CSV file representing an event log and return it as a pandas DataFrame.

    This function reads the specified CSV file and returns its contents as a pandas DataFrame,
    representing an event log. The event log contains records of various events with associated
    information such as case ID, activity, and timestamps.

    Parameters:
        file (str): The filename (including the path) of the CSV file to be loaded.

    Returns:
        pandas.DataFrame: A DataFrame representing the event log read from the specified CSV file.

    """
    
    event_log = pd.read_csv(os.path.join(file_path_csv, file), sep =',')
    num_events = event_log.shape[0]
    num_cases = len(event_log.caseID.unique())
    num_activities = len(event_log.activity.unique())
    print("Number of events:    {}\nNumber of cases:      {}\nNumber of activities: {}".format(num_events, num_cases,num_activities))
    event_log.head(5)
    
    return event_log



def pre_processing(event_log, parameter = True):
    
    """
    Pre-processes an event log DataFrame for process mining by merging state and activity/action information
    into a single column, updating activity names, creating a timestamp column, and applying final pre-processing
    to prepare the data for the process mining algorithm.

    Parameters:
        event_log (pd.DataFrame): The input event log as a pandas DataFrame with the following columns:
                                  'caseID', 'activity', 'state', 'time', and additional columns representing
                                  boolean states.
        parameter (bool, optional): A boolean parameter indicating whether to include 'noMoreStepsNecessary'
                                    activities in the pre-processing. Default is True.

    Returns:
        pd.DataFrame: Pre-processed DataFrame with merged activity and state information and additional columns.
        set: A set of activities for which the names were changed during pre-processing.
                
     """

    case_ids = list(event_log.caseID.unique())
    print(len(case_ids))


    df = event_log.iloc[:, 3:-2]#reduced dataframe with no activity column and states just boolean columns

    list_names_columns = list(df)#list names columns reduced dataframe

    unique_states =  set(list(event_log.state.unique()))

    unique_activities=  set(list(event_log.activity.unique()))

    activities_changed = set()

    list_sequences = []
    for i in range(len(case_ids)):


        data = event_log[event_log.caseID == case_ids[i]]#save the entire sequence of an caseID

        if data.state.iloc[-1] == 'Start': print(case_ids[i])

        case = list(data.caseID)
        list_time = list(data.time)
        list_activity = list(data.activity)
        list_time =  list(data.time)
        list_state = list(data.state)


        temp = []
        count =0 #to update the time


        for j in range(len(list_state)):
            
            
            if list_activity[j] == 'noMoreStepsNecessary' and parameter is True:
                continue


            else:

                if  list_activity[j] == 'deadlock' and list_state[j] != 'Complete':
                    row_list = df.loc[j].tolist()
                    temp_2 = [case[j], count, list_activity[j]]
                    temp_2.extend(row_list[:])
                    temp.append(temp_2)
                    count += 1
                    #temp.append([case[j], count, list_activity[j]])
                    #count += 1

                elif  list_activity[j] == 'deadlock' and list_state[j] == 'Complete':#drop the last row when the simulation ended with Complete
                    continue

                elif list_activity[j] != 'reset':#reset is the intilaization of the simulator
                    row_list = df.loc[j].tolist()
                    temp_2 = [case[j], count, list_activity[j]+'_'+list_state[j -1] +'_'+ list_state[j]]
                    temp_2.extend(row_list[:])
                    temp.append(temp_2)#action_destination
                    count += 1
                    
                    
                    temp_2 = [case[j], count, list_state[j]]
                    temp_2.extend(row_list[:])
                    temp.append(temp_2)
                    activities_changed.add(list_activity[j]+'_'+list_state[j -1] +'_'+ list_state[j])

                else:
                    
                    row_list = df.loc[j].tolist()
                    temp_2 = [case[j], count, list_activity[j]+'_'+ list_state[j]]
                    temp_2.extend(row_list[:])
                    temp.append(temp_2)
                    count += 1
                    
                    temp_2 =[case[j], count, list_state[j]]
                    temp_2.extend(row_list[:])
                    temp.append(temp_2)
                    count += 1
                    activities_changed.add(list_activity[j] +'_'+ list_state[j])

        list_sequences.extend(temp)

    #create list with the names of columns
    list_case_time_activity = ['caseID', 'time', 'activity']
    list_case_time_activity.extend(list_names_columns)# add the name of the columns reduced dataframe

    df_new = pd.DataFrame(list_sequences, columns = list_case_time_activity)#new dataframe with a column for the activities and states

    df_new.head(5)
    
    #final pre-processing of the event log data
    event_log_plus_modes = df_new
    num_events = event_log_plus_modes.shape[0]
    num_cases = len(event_log_plus_modes.caseID.unique())
    num_activities = len(event_log_plus_modes.activity.unique())
    
    #creates a column timeStamp from the time column
    event_log_plus_modes['timestamp'] = event_log_plus_modes['time'] + event_log_plus_modes['time'] + 1617295944.17324
    event_log_plus_modes['date'] =pd.to_datetime(event_log_plus_modes.timestamp,unit='s', origin='unix')
    
    event_log_plus_modes_activity = pm4py.format_dataframe(event_log_plus_modes, case_id= 'caseID', activity_key='activity' , timestamp_key= 'date', timest_format= '%Y-%m-%d %H:%M:%S%z')
    
    return df_new, activities_changed


def call_hm_algorithm(event_log_plus_modes_activity, display_pm = True ):
   
    """
    Applies the Heuristic Miner algorithm on the pre-processed event log data and optionally displays the process model.

    Parameters:
        event_log_plus_modes_activity (pm4py.objects.log.util.DataFrame): The pre-processed event log as a PM4PY DataFrame,
                                                                         with the required columns.
        display_pm (bool, optional): A flag to control whether to display the mined process model.
                                     If True, the process model will be displayed using the Heuristic Miner visualizer.
                                     Default is True.

    Returns:
        pm4py.objects.heuristics_net.HeuristicsNet: The Heuristic Miner model representing the mined process model.

    """
    # heuristics miner
    heu_net = heuristics_miner.apply_heu(event_log_plus_modes_activity,parameters={ "dfg_pre_cleaning_noise_thresh": 0})

    # viz
    if display_pm:
        gviz = hn_visualizer.apply(heu_net)
        hn_visualizer.view(gviz)

    return heu_net




def convert_hm_model_to_string(heu_net):
    
    """
    Converts the Heuristic Miner model to a string representation in dot format.

    Parameters:
        heu_net (pm4py.objects.heuristics_net.HeuristicsNet): The Heuristic Miner model.

    Returns:
        str: A string representation of the Heuristic Miner model in dot format.

    """
    
    #transforms heu_net in dot file
    dot_file = hn_visualizer.get_graph(heu_net)
    
    # As a bytes literal:
    output_graphviz_dot = dot_file.create_dot()
    
    #from dot to data format
    graph = pydotplus.graph_from_dot_data(output_graphviz_dot)

    #to string format
    data = graph.to_string()
    
    return data
    

def parse_dot_string(data):
    
    """
    Parses the string representation of a dot file containing a Heuristic Miner model.

    Parameters:
        data (str): The string version of the dot file representing the Heuristic Miner model.

    Returns:
        list: A list of edges in the Heuristic Miner model, where each edge is represented as a tuple (origin, destination).
        list: A list of labels associated with the edges in the Heuristic Miner model.
        list: A list of binary node names used in the dot file.
 
    """
    data = pgv.AGraph(data)
    edges_origin_dest =  []
    for e in data.edges():
        edges_origin_dest.append(e)

    labels = []    
    for e in data.nodes():
        if 'label' in e.attr:
            labels.append(e.attr['label'])
    labels.remove('\\N')

    binary_names = []        
    for node in data.nodes():
        binary_names.append(node)
        
    return edges_origin_dest, labels, binary_names

def save_uniques_acivities(activities_changed, labels):
    
    """
    Checks the activities with name changed during the pre-processing step against the labels parsed from the dot file
    of the Heuristic Miner model. If they are present, it saves them in a list with their corresponding frequencies.

    Parameters:
        activities_changed (set): A set of activities with name changed during the pre-processing step.
        labels (list): A list of labels parsed from the dot file of the Heuristic Miner model.

    Returns:
        list: A list of unique activities with their names changed during pre-processing and their corresponding frequencies.

    
    """
    #save in a list the activities and outcomes (add or fail)
    #needed to create the list that includes the transitions system TODO

   
    list_unique_activities = []
    temp_unique_activities = list(activities_changed.copy())
    for i in labels:
        lb = i.split(' ')[0]
        for j in activities_changed:
            if lb == j:
                list_unique_activities.append(i)

    return list_unique_activities


def match_binary_names_labels(edges_origin_dest, binary_names, labels):
    
    """
    function that matches the binary names with original names and save them in a list
    i.e., from 'cefbcdb9-ceeb-4847-8208-8677f91f67b6' to 'Start'
    
    Input: 1) binary_names - list of names of the nodes used in th dot file
           2) labels - lables parsed from the dot file of the HM model
            
    Return: 1) edges_origin_dest_labels - list of matched edges with their original names 
    """
    
    
    #here save in a list where the code names of the nodes are converted in the original names
   
    labels_names_inv = dict(zip(binary_names, labels))#creates a dictionary - keys the binary names and values label names
    edges_origin_dest_labels = []
    for i in range(len(edges_origin_dest)):
        temp = []
        for j in range(len(edges_origin_dest[i])):
            temp.append(labels_names_inv[edges_origin_dest[i][j]])
        edges_origin_dest_labels.extend(tuple([temp]))

    return edges_origin_dest_labels



def match_origin_destination_activity(edges_origin_dest_labels, list_unique_activities):

    """
    Matches the origin and destination states and the activity used to move between them and saves the results in a list.
    The list is needed to create the dataset used to construct nodes, edges, and labels for the graph.

    Parameters:
        edges_origin_dest_labels (list): A list of matched edges with their original names.
        list_unique_activities (list): A list of unique activities with their names changed and their corresponding frequencies.

    Returns:
        list: A list of tuples containing matched origin and destination states with the correct activity label.
    
    """
    

    nmp_edges_origin_dest_labels= np.array(edges_origin_dest_labels)
    number_tot_rows = set(list(range(len(nmp_edges_origin_dest_labels))))

    list_activity_labels = []
    rows = []
    list_nodes = []
    for activity in list_unique_activities:
        
        #search and match giving the indexes of the actions\activities found
        result = np.where(nmp_edges_origin_dest_labels==activity)
        #split the values of the results of np.where in two
        zero = result[0].tolist()#gives the number of the coluns where found it
        one = result[1].tolist()#gives the rows

        row_first_found = nmp_edges_origin_dest_labels[zero[0]].tolist()
        row_second_found = nmp_edges_origin_dest_labels[zero[1]].tolist()
        rows.append(zero[0])
        rows.append(zero[1])

        if row_first_found[0] !=activity:
            list_activity_labels.append([(row_first_found[0],row_second_found[1]),activity])

    rows_set = set(rows)
    left_out_rows = number_tot_rows - rows_set

    #need to add elements that have no actions as outcomes that are left out
    for j in left_out_rows:
        temp = nmp_edges_origin_dest_labels[j].tolist()
        list_activity_labels.append([(temp[0], temp[1]), 'no_label'])#add a label

    
    return list_activity_labels


def list_edges(list_activity_labels):
    
    """
    Creates the final version of the list that represents the origin, destination, action, and value (frequencies).
    The value corresponds to the number of times the path from the origin to the destination through the action was taken in simulations.

    Parameters:
        list_activity_labels (list): A list of tuples containing matched origin and destination states with the correct activity labels.

    Returns:
        list: A list of tuples representing the final version of edges, where each tuple contains the origin state, destination state,
              action, and its corresponding value (frequencies).

    """
    
    list_edges =  []
    for i in range(len(list_activity_labels)):
        origin = list_activity_labels[i][0][0].split(' ')[0]
        dest = list_activity_labels[i][0][1].split(' ')[0]
        action =  list_activity_labels[i][1].split(' ')[0]

        if action != 'no_label':
            freq_origin = int(list_activity_labels[i][0][0].split(' ')[1].strip('()'))
            freq_dest = int(list_activity_labels[i][1].split(' ')[1].strip('()'))
            value = round(freq_dest / freq_origin, 3)
        else:
            value = '-'

        list_edges.append([(origin, dest), action, value])
    return list_edges

def check_deadlocks(list_for_nodes_edges):
    found = False

    # Iterate through the lists in reverse order
    for sublist in reversed(list_for_nodes_edges):
        # Iterate through the tuples in reverse order
        for item in reversed(sublist):
            # Check if the item is a tuple and contains the word "deadlock"
            if isinstance(item, tuple) and "deadlock" in item:
                found = True
                break
 
        # If the word is found, break out of the outer loop as well
        if found:
            break

    # Print the result
    if found:
        #print("There is at least a 'deadlock' present in the model.")
        return True
    else:
        #print("There is no 'deadlock' present in the model.")
        return False


def  parse_dot_simulation_model(file):
    
    """
    Parses the dot file representing the SIMULATION Ris/QFLan model, which represents the formal model's behavior.

    Parameters:
        file (str): The path to the dot file of the SIMULATION Ris/QFLan model.

    Returns:
        str: A string representation of the SIMULATION Ris/QFLan model in dot format.
-
    """
    graphs = pydot.graph_from_dot_file(os.path.join(file_path_dot, file))
    graph = graphs[0]
    output_graphviz_dot_1 = graph.create_dot()
    graph_2 = pydotplus.graph_from_dot_data(output_graphviz_dot_1)
    
    data = graph_2.to_string()
    
    return data

def parse_dot_string_2(data):
    
    """
    Parses the dot data representing the Mined PM model.

    Parameters:
        dot_data (str): The dot data representing the Mined PM model.

    Returns:
        list: A list of labels extracted from the dot data.
        list: A list of edges extracted from the dot data.
    
    """
    
    data = pgv.AGraph(data)
    edges_origin_dest_old =  []
    for e in data.edges():
        edges_origin_dest_old.append(e)


    labels_old = []
    for e in data.edges():
        if 'label' in e.attr:
            labels_old.append(e.attr['label'])
            
    return edges_origin_dest_old, labels_old

def pop_empty_string(edges_origin_dest_old, labels_old):
    
    """
    Drops empty strings '' from lables _old list 
    that rerpresents in the dot file the definition of the subgraph
    
    """
    
    for index, element in enumerate(labels_old):
        if element == '':
            labels_old.pop(index)
            edges_origin_dest_old.pop(index)
    
    return edges_origin_dest_old, labels_old




def match_orig_dest_act_old_RisQFLan(edges_origin_dest_old, labels_old):
    
    """
    Matches the origin and destination states and the activity used to move between them and saves the results in a list.
    This function is specifically designed for the RisQFLan model.

    Parameters:
        edges_origin_dest_labels (list): A list of matched edges with their original names.
        labels (list): A list of labels associated with the edges.

    Returns:
        list: A list of tuples containing matched origin and destination states with the correct activity to create a DataFrame.
    
    """

    list_dataframe =[]

    no_labels_list = ['@@S', '@@E']#@@S could be dropped
    for i in range(len(edges_origin_dest_old)):
        if edges_origin_dest_old[i][0] not in no_labels_list and  edges_origin_dest_old[i][1] not in no_labels_list:
            list_dataframe.append([edges_origin_dest_old[i][0], edges_origin_dest_old[i][1], labels_old[i].split(',')[0], labels_old[i].split(',')[1] ])
        else:
            if edges_origin_dest[i][1] == '@@E':
                list_dataframe.append([edges_origin_dest_old[i][0], edges_origin_dest_old[i][1], '', '-' ])
                
                
    return list_dataframe


def list_edges_old(list_dataframe):
    
    """
    Creates a list that represents the origin, destination, action, and value (weight) for a specific path in the Rated transition system.
    The weight corresponds to the value given to a specific path in the Rated transition system.

    Parameters:
        list_dataframe (list): A list containing tuples representing the matched origin and destination states with the correct activity.

    Returns:
        list: A list of tuples representing the origin, destination, action, and weight for each path in the Rated transition system.
 
    """
    
    list_edges =  []
    for i in range(len(list_dataframe)):
        origin = list_dataframe[i][0]
        dest = list_dataframe[i][1]
        action =  list_dataframe[i][2]
        value =  list_dataframe[i][3]


        list_edges.append([(origin, dest), action, value])
    return list_edges

def prepare_both_transition_system_RisQFLan(list_for_nodes_edges_old, list_for_nodes_edges):

    """
    Creates two dictionaries of both transition systems: MINED SIMULATION RisQFLan MODEL and SIMULATION RisQFLan MODEL.
    This function is designed specifically for the RisQFLan model.

    Parameters:
        list_for_nodes_edges (list): A list representing the complete simulated transition system.
        list_for_nodes_edges_old (list): A list representing the complete original transition system.

    Returns:
        dict: A dictionary representing the simulated transition system.
        dict: A dictionary representing the original transition system.
    """
    
    dict_old = {}
    for i in range(len(list_for_nodes_edges_old)):
        if list_for_nodes_edges_old[i][1] != 'try':
            dict_old[(list_for_nodes_edges_old[i][0][0],list_for_nodes_edges_old[i][0][1], list_for_nodes_edges_old[i][1].split('_')[0] )]= list_for_nodes_edges_old[i][2]
        else:
            dict_old[(list_for_nodes_edges_old[i][0][0],list_for_nodes_edges_old[i][0][1], 'tryAction' )]= list_for_nodes_edges_old[i][2]    

    #####  DROPS @@E 
    dict_new = {}
    for i in range(len(list_for_nodes_edges)):
        if list_for_nodes_edges[i][1] != 'no_label':
            if list_for_nodes_edges[i][0][1] != '@@E':
                dict_new[(list_for_nodes_edges[i][0][0],list_for_nodes_edges[i][0][1], list_for_nodes_edges[i][1].split('_')[0] )]= list_for_nodes_edges[i][2]
            else:
                continue
        elif list_for_nodes_edges[i][0][1] == '@@E':
            continue
        else:
            dict_new[(list_for_nodes_edges[i][0][0],list_for_nodes_edges[i][0][1], '')]= list_for_nodes_edges[i][2]

    return dict_old, dict_new


def diff(dfg_old, dfg_new):
    """
    Calculates the difference between two Directed Frequency Graphs (DFGs) and returns the results as dictionaries.

    Parameters:
        dfg_old (dict): A dictionary representing the reference Directed Frequency Graph (DFG).
        dfg_new (dict): A dictionary representing the DFG created with simulated evento log.

    Returns:
        dict: A dictionary containing the comparison results between the reference and test DFGs.
        dict: A dictionary containing the differences in frequencies between the reference and test DFGs.
        
    """
    dfg_result = {}
    dfg_result_new = {}#dictionary to save the difference between the frequencies of the two graph
    
    for edge in dfg_old:
        if edge in dfg_new:
            dfg_result[edge] = 'ok'
            if dfg_old[edge] != '-':
                count = round(float(dfg_old[edge]) - float(dfg_new[edge]),3)
                dfg_result_new[edge] = count
            
        else:
            dfg_result[edge] = 'missing'
            dfg_result_new[edge] = ''
    
    for edge in dfg_new:
        if edge not in dfg_old:
            dfg_result[edge] = 'extra'
            
    
    return dfg_result, dfg_result_new


def draw_diff_freq(dfg_diff, dfg_freq, name):
    
    #NOT IN USE YET

    dot = graphviz.Digraph(name)
    activities = {a for (a,b,l) in dfg_diff}.union({b for (a,b,l) in dfg_diff})
    outgoing_nodes = lambda node,dfg,status : len({(a,b) for (a,b,l) in dfg if a==node and dfg[(a,b,l)] == status})
    incoming_nodes = lambda node,dfg,status : len({(a,b) for (a,b,l) in dfg if b==node and dfg[(a,b,l)] == status})
    red_activities = {a for a in activities if 
                (outgoing_nodes(a,dfg_diff,'missing') > 0 and incoming_nodes(a,dfg_diff,'missing') > 0) or
                (outgoing_nodes(a,dfg_diff,'extra') > 0 and incoming_nodes(a,dfg_diff,'extra') > 0)}

    for a in activities:
        if a in red_activities or a == 'deadlock':
            dot.node(a, color='red',fontcolor='red')

    for key in dfg_diff:
        color = 'black' if dfg_diff[key] == 'ok' else 'red'
        style = 'dashed' if dfg_diff[key] == 'missing' else 'solid'
        if key[2] != 'no':
            dot.edge(key[0], key[1], color=color, style=style, label=key[2]+' '+ str(dfg_freq[key]))
        else:
            dot.edge(key[0], key[1], color=color, style=style, label='')

    return dot

def draw_diff(dfg_diff, name):
    
    path = file_path_results
    dot = graphviz.Digraph(path + name,node_attr = {'fontname':'Comic Sans MS'})
    activities = {a for (a,b,l) in dfg_diff}.union({b for (a,b,l) in dfg_diff})
    outgoing_nodes = lambda node,dfg,status : len({(a,b) for (a,b,l) in dfg if a==node and dfg[(a,b,l)] == status})
    incoming_nodes = lambda node,dfg,status : len({(a,b) for (a,b,l) in dfg if b==node and dfg[(a,b,l)] == status})
    red_activities = {a for a in activities if 
                (outgoing_nodes(a,dfg_diff,'missing') > 0 and incoming_nodes(a,dfg_diff,'missing') > 0) or
                (outgoing_nodes(a,dfg_diff,'extra') > 0 and incoming_nodes(a,dfg_diff,'extra') > 0)}

    for a in activities:
        if a in red_activities or a == 'deadlock':
            dot.node(a, color='red',fontcolor='red',fontname='Comic Sans MS')

    for key in dfg_diff:
        color = 'black' if dfg_diff[key] == 'ok' else 'red'
        style = 'dashed' if dfg_diff[key] == 'missing' else 'solid'
        dot.edge(key[0], key[1], color=color, style=style, label=key[2])
    dot.graph_attr['ratio'] = 'auto'
    dot.graph_attr['size'] = '100,100'
    
    if len(dfg_diff) == 0:
        dot.node('There are no differences between the formal model and the simulated one!', color = 'white')
        
    
    return dot

def imp_edges_modified(diff_dict):
    
    """
    function that drops the edges over the same nodes that are present in both DFGs
    making the new DFG more readable.
    
    Input: 1) diff_dict - dictinary with all the edges and nodes retrieved by comparing the two DFGs
    
    Return: 1) new_dfg_diff - dictinary with only the most important edges bewteen the nodes
    
    ### ONLY QFLan ###
    
    """
    new_dfg_diff = {}
    for key, v in diff_dict.items():
        if v != 'ok':#  or ( (key[0] ==key[1] and key[2] == 'install(Cappuccino)') or (key[0] ==key[1] and key[2] == 'uninstall(Cappuccino)')) or key[0] !=key[1]:
            new_dfg_diff[key] = v
    return new_dfg_diff

def draw_diff_initial(dfg_diff, name, list_initial):
    
    """
    Function draws a diff model with, if any, initial knowledge which aere simple nodes already gaiend by the attacker
    
    - dashed red edges: edges that the simulator has not traversed
    - solid (continue) red edges: new edges that the original model did not have
    - solid blue edges and nodes: represent nodes with edges that are not traversed 
        by the simulator because already gained by the attacker 
    
    """
    
    new_dict = {}

    # Extracts unique keys from key[0] and key[1]
    unique_keys = set()
    for key, _ in dfg_diff.items():
        unique_keys.add(key[0])
        unique_keys.add(key[1])

    # For each unique key, searches in the old dict and save the values in the new one
    for unique_key in unique_keys:
        values_list = []
        for key, value in dfg_diff.items():
            if unique_key in key:
                values_list.append(value)
        new_dict[unique_key] = values_list

    #print()

    for key, value in dfg_diff.items():
        if key[0][3:].lower() in list_initial or key[1][3:].lower() in list_initial or key[2][4:-1].lower() in list_initial or key[2][5:-1].lower() in list_initial:
            if value == 'missing':
                dfg_diff[key] = 'initial_knowledge'
    
    
    path = file_path_results
    dot = graphviz.Digraph(path + name)#,node_attr = {'fontname':'Comic Sans MS'})
    dot.attr('node', shape='box', style =  'rounded',penwidth='1.75')
    dot.attr(rankdir='LF')

    activities = {a for (a,b,l) in dfg_diff}.union({b for (a,b,l) in dfg_diff})
    outgoing_nodes = lambda node,dfg,status : len({(a,b) for (a,b,l) in dfg if a==node and dfg[(a,b,l)] == status})
    incoming_nodes = lambda node,dfg,status : len({(a,b) for (a,b,l) in dfg if b==node and dfg[(a,b,l)] == status})
    red_activities = {a for a in activities if 
                (outgoing_nodes(a,dfg_diff,'missing') > 0 and incoming_nodes(a,dfg_diff,'missing') > 0) or
                (outgoing_nodes(a,dfg_diff,'extra') > 0 and incoming_nodes(a,dfg_diff,'extra') > 0)}
    blue_activities = {a for a in activities if 
                (incoming_nodes(a,dfg_diff,'Inital_knowledge') > 0)}
    
    
    for a in activities:
        if a in red_activities or a == 'deadlock' or (new_dict[a].count('missing') == len(new_dict[a]) and a[3:] not in list_initial):
            dot.node(a, color='red',fontcolor='red')#,fontname='Comic Sans MS')    
        if a[3:] in list_initial:
            dot.node(a, color='blue',fontcolor='blue')#,fontname='Comic Sans MS')


    for key in dfg_diff:
        if dfg_diff[key] == 'ok':
            color = 'black' 
        elif dfg_diff[key] == 'missing' or  dfg_diff[key] == 'extra':
            color ='red'
        elif dfg_diff[key] == 'initial_knowledge':
            color = 'green'
        style = 'dashed' if dfg_diff[key] == 'missing' else 'solid'
        dot.edge(key[0], key[1], color=color, style=style, label=key[2],  penwidth='1.75')
    dot.graph_attr['ratio'] = 'auto'
    dot.graph_attr['size'] = '80,60'
    dot.attr(rankdir='TB')
    
    if len(dfg_diff) == 0:
        dot.node('There are no differences between the formal model and the simulated one!', color = 'white')
    
        
    
    return dot





def extract_everything_from_bbt(bbt_file):
    
    with open(os.path.join(file_path_bbt, bbt_file)) as file:
        attack_diagram = []
        defense_nodes = []
        countermeasure_nodes = []
        init_node = []
        transitions = []
        action_constraints = []
        attributes = []
        actions = []
        quantitative_constraints = []
        model_name = ""  
        attack_nodes = []  # New list to store attack nodes
        
        
        
        read_attack_diagram = False
        read_defense_nodes = False
        read_countermeasure_nodes = False
        read_init_nodes = False
        read_transitions = False
        read_action_constraints = False
        read_attributes = False
        read_actions = False
        read_quantitative_constraints = False
        read_attack_nodes = False  # Flag for reading attack nodes

        for line in file:
            line = line.lstrip('\t')  # Remove leading tabs
            line = line.strip()  # Remove leading and trailing spaces

            if 'begin attack diagram' in line:
                read_attack_diagram = True
            elif 'end attack diagram' in line:
                read_attack_diagram = False
                continue

            if 'begin model' in line:
                # Estrai il nome del modello dalla stessa linea
                match = re.search(r'begin model (\w+)', line)
                if match:
                    model_name = match.group(1)

            if read_attack_diagram and 'begin attack diagram' not in line and 'end attack diagram' not in line:
                attack_diagram.append(line)

            if 'begin defense nodes' in line:
                read_defense_nodes = True
            elif 'end defense nodes' in line:
                read_defense_nodes = False
                continue

            if read_defense_nodes and 'begin defense nodes' not in line and 'end defense nodes' not in line:
                defense_nodes.append(line)

            if 'begin countermeasure nodes' in line:
                read_countermeasure_nodes = True
            elif 'end countermeasure nodes' in line:
                read_countermeasure_nodes = False
                continue

            if read_countermeasure_nodes and 'begin countermeasure nodes' not in line and 'end countermeasure nodes' not in line:
                line = line.replace(' = ', '=')
                countermeasure_nodes.append(line)

            if 'begin init' in line:
                read_init_nodes = True
                continue

            if read_init_nodes and 'begin init' not in line and 'end init' not in line:
                if '//' not in line and line.strip():
                    init = re.findall(r'{(.*?)}', line)
                    if init:
                        init = init[0].split(',')
                        init_node.extend(init)

            if 'transitions =' in line:#the transitions has to be below the line with transitions = 
                read_transitions = True
                transitions = []  # Clear the transitions list
                continue  # Skip the line containing 'transitions ='

            if read_transitions and 'end attack' in line:
                read_transitions = False  # Stop reading transitions
                continue

            if read_transitions and line.strip():  # Exclude empty lines
                transitions.append(line)

            if 'begin action constraints' in line:
                read_action_constraints = True
                continue

            if read_action_constraints and 'end action constraints' in line:
                read_action_constraints = False  # Stop reading action constraints
                continue

            if read_action_constraints and line.strip():  # Exclude empty lines
                action_constraints.append(line)

            if 'begin attributes' in line:
                read_attributes = True
                continue

            if read_attributes and 'end attributes' in line:
                read_attributes = False  # Stop reading attributes
                continue

            if read_attributes and line.strip():  # Exclude empty lines
                attributes.append(line)

            if 'begin actions' in line:
                read_actions = True
                #actions = []  # Clear the actions list
                continue

            if read_actions and 'end actions' in line:
                read_actions = False  # Stop reading actions
                continue

            if read_actions and line.strip():  # Exclude empty lines
                actions.append(line.split())
                
            
            if 'begin quantitative constraints' in line:
                read_quantitative_constraints = True
            elif 'end quantitative constraints' in line:
                read_quantitative_constraints = False
                continue
            
            if read_quantitative_constraints and 'begin quantitative constraints' not in line and 'end quantitative constraints' not in line:
                quantitative_constraints.append(line)
                
            # Add new condition to handle attack nodes
            if 'begin attack nodes' in line:
                read_attack_nodes = True
            elif 'end attack nodes' in line:
                read_attack_nodes = False
                continue

            if read_attack_nodes and 'begin attack nodes' not in line and 'end attack nodes' not in line:
                attack_nodes.append(line)
 

    attributes = [att for att in attributes if '//' not in att and att != '']
    transitions = [trans for trans in transitions if '//' not in trans and trans != '']
    attributes = ' '.join(attributes)
    quantitative_constraints = [cons for cons in quantitative_constraints if '//' not in cons and cons != '']
    quantitative_constraints = ' '.join(quantitative_constraints)
    # Split each string into individual words
    attack_nodes = [word for phrase in attack_nodes for word in phrase.split()]
    
    # Filter countermeasure nodes
    filtered_attack_diagram = []
    for i in countermeasure_nodes:
        for j in attack_diagram:
            if i.split('=')[0] not in j:
                filtered_attack_diagram.append(j)

    # Filter defense nodes
    final_attack_diagram = []
    for i in defense_nodes:
        for j in filtered_attack_diagram:
            if i not in j:
                final_attack_diagram.append(j)
                
    list_elements_bbt = [attack_diagram, defense_nodes, countermeasure_nodes, 
            init_node, transitions, action_constraints, attributes, actions, model_name, final_attack_diagram]

    dict_bbt = {}
    
    transitions = clean_strings(transitions)#cleans the srings from extra spaces
    
    attack_diagram = [s for s in attack_diagram if s != ""]
    
    # Reghular expression to dived the strings
    pattern_states = r'(\w+|-\(.*?\)->|\w+)' #extracts the states from the transitions

    # divedes each transition in three separate elements, origin, actions with the conditions and destination
    results = [re.findall(pattern_states, string) for string in transitions]#transitions from the BBT file 
  
    # Extract the unique element no the actions  
    unique_el = set()

    for trans in results:
        unique_el.add(trans[0])
        unique_el.add(trans[-1])

    # convert the set in a list
    states = list(unique_el)


    dict_bbt['attack_diagram'] = attack_diagram
    dict_bbt['transitions'] = transitions
    dict_bbt['defense_nodes'] = defense_nodes
    dict_bbt['countermeasure_nodes'] = countermeasure_nodes
    dict_bbt['action_constraints'] = action_constraints
    dict_bbt['quantitative_constraints'] = quantitative_constraints
    dict_bbt['attributes'] = attributes
    dict_bbt['actions'] = actions[0]
    dict_bbt['model_name'] = model_name
    dict_bbt['init_node'] = init_node
    dict_bbt['final_attack_diagram'] = final_attack_diagram
    dict_bbt['attack_nodes'] = attack_nodes
    dict_bbt['states'] = states
    dict_bbt['name_properties'] = attack_nodes #for now they are all the nodes but it should be better to includes only root and parent node

    
    return dict_bbt




def clean_strings(string_list):
    
    """Function cleans the transition system from extra spaces that cerats problems to use the
        "fix_transition_system"   function   
    """
    new_list = []

    for string in string_list:
        new_string = re.sub(r'\s*-\s*\(\s*', ' -(', string)
        new_string = re.sub(r'\s*\)\s*->\s*', ')-> ', new_string)
        new_list.append(new_string)
    
    return new_list


import re

import copy 

def fix_transition_system_original_weights(list_for_nodes_edges, dict_bbt):
    
    """ function that update the transition system 
        adds transitions that fix deadlocks, if any.
        
        input: 1) list_for_nodes_edges - list of edges with [[(origin, destimation),
          'action_origin_destimation', ... from the simualtions
               2) dict_bbt - dictinary with the information extracted from the bbt file
        output: 1) final_transtions - list of the updated transitions with the new weights taken from the simualtions
                                    and the new transitions fro the deadlocks, if any
                2) dict_bbt - dictionary with the updatated name of the model and the new action 'goBack' if there are deadlocks
    """
    
    list_transitions = copy.deepcopy(list_for_nodes_edges)
    dict_bbt_copy = copy.deepcopy(dict_bbt)
    
    #drop from the transitions system extracted from the simulations the edges between a node and the end node creted using PM
    transition_simulations = []
    for edge in list_transitions:
        if edge[0][1] == '@@E':#drops the lists that includes 
            continue
        else:
            transition_simulations.append([edge[0][0].split(' ')[0], edge[1].split('_')[0], edge[2], edge[0][1].split(' ')[0]])

    #sorts the transition system from the simualtions
    sorted_data_sim = sorted(transition_simulations, key=lambda x: (x))

    #creates a dictionary with the deadlock where the keys are the indexes of the transition system simulated
    dictionary_deadlock = {}
    for index, item in enumerate(sorted_data_sim):
        if item[-1] == 'deadlock':
            dictionary_deadlock[index] = item

    # List to save corresponding lists
    new_list = []

    # Loop through the dictionary
    for key, value in dictionary_deadlock.items():
        first_element = value[0]

        # Find lists in the list_of_lists that match the criteria
        matching_lists = [lst for lst in sorted_data_sim if lst[0] == first_element and (lst[1].startswith('add') or lst[1].startswith('succ') or lst[1].startswith('fail'))]
        new_list.extend(matching_lists)


    # Initialize a set to keep track of unique elements
    unique_elements = set()

    # List to save unique lists
    list_trans_deadlocked_sim = []

    # Loop through the list of lists
    for lst in new_list:
        first_element = lst[0]
        third_element = lst[3]

        # Create a unique key based on the first and third element
        unique_key = (first_element, third_element)

        # If the unique key is not already in the set, add the list to list_trans_deadlocked_sim and add the key to the set
        if unique_key not in unique_elements:
            unique_elements.add(unique_key)
            list_trans_deadlocked_sim.append(lst)

    #if list_trans_deadlocked_sim is not empty we need to add a new action 'goBack' in actions list
    #and chenge the name of the model by adding 'Refined'

    if list_trans_deadlocked_sim != []:
        actions = dict_bbt_copy['actions']
        actions.append('goBack')
        dict_bbt_copy['actions'] = actions
        name = dict_bbt_copy['model_name']
        name +='Refined'
        dict_bbt_copy['model_name'] = name

    # Reghular expression to dived the strings
    pattern = r'(\w+|-\(.*?\)->|\w+)'

    # divedes each transition in three separate elements, origin, actions with the conditions and destination
    results = [re.findall(pattern, string) for string in dict_bbt['transitions']]#transitions from the BBT file 
    
    #filters only the transitions (from the simulations) that do not have deadlocks
    filtered_data_list = [item for item in sorted_data_sim if item[-1] != 'deadlock']

    # Create a dictionary to map the specified conditions in the first list
    condition_mapping = {(item[0], item[-1], item[1]) for item in results}

    # Sort the second list based on the conditions
    sorted_second_list = sorted(filtered_data_list, key=lambda item: (item[0], item[-1], item[1]) in condition_mapping)

    #save only the new weights from the simulations
    second_elements = [item[2] for item in sorted_second_list]

   
    #add gooback transition to the parents nodes into the transition system
    goback_acition = '-(goBack, 0.001)->'

    list_goback_edges = []

    for deadlock in list_trans_deadlocked_sim:
        list_goback_edges.append([deadlock[0], goback_acition, deadlock[-1]])

  

    #creats a dict with the indexes of where to find the edges to insert the new transitions goback 
    dict_edges = {}
    for goback_edge in list_goback_edges:
        key = goback_edge[0]
        dict_edges[key] = []
        for index, res in enumerate(results):
            if goback_edge[0] == res[0] and goback_edge[-1] == res[-1]:
                dict_edges[key].append(index)


    count = 0
    for key, value in dict_edges.items():
        for goback_edge in list_goback_edges:
            if key == goback_edge[0]:
                #print(value[-1])
                #insert the new transitions after the last edges with the same origin and destation of the goback transition
                results.insert(value[-1]+1+ count, goback_edge)
                count += 1

    final_transitions = [' '.join(ls) for ls in results]


    return final_transitions, dict_bbt


def view_AB_refined(states, transition_system , model_name):
    
    """
    Function the prompts the user of the graphical rep of the attacker behavior model
    when creating the bbt file
    
    Input: 1) list of states - i.e., Start, Complete, Try...
           2) list of tranistions refined 
    
    
    """

    # Regular expression pattern to divide the strings
    pattern = r'(\w+|-\(.*?\)->|\w+)'

    # Divides each transition into three separate elements: origin, actions with conditions, and destination
    results = [re.findall(pattern, string) for string in transition_system]

    # Extract only the desired part from the second element
    pattern_extract = r'\(([^,]+,\s\d+(\.\d+)?)|([^,]+,\s\.\d+),'
    extracted_data = [re.search(pattern_extract, item[1]).group(1) if re.search(pattern_extract, item[1]) else None for item in results]

    # Create a nested list of lists with the desired second element
    edges_and_labels = [[item[0], extracted_data[i], item[-1]] for i, item in enumerate(results)]
   
    name = model_name
    dot = graphviz.Digraph(name)
    dot.attr('node', shape='box', style =  'rounded',color='blue', penwidth='2.0')
    dot.attr(label='Preview Attacker Behavior Refined',labelloc ='t', labeljust='c', fontsize='22', fontcolor = 'black')
    


    for st in states:
        dot.node(st)
    for ed in edges_and_labels:
        if ed[1] is not None and 'goBack' in ed[1]:
            dot.edge(ed[0], ed[2], color='orange',  label=ed[1],  penwidth='2')
        else:
            dot.edge(ed[0], ed[2], color='blue',  label=ed[1],  penwidth='2.0')
    dot.graph_attr['ratio'] = 'auto'
    dot.graph_attr['size'] = '100,100'
    
    dot.render(filename='./data/refined_BBT/preview_AB/'+f'Preview_AB_Refined_{name}', format='pdf', cleanup=True)

    return dot


def refined_bbt(dict_bbt, final_transitions):    
    
    from jinja2 import Template
    from jinja2 import Template

    #with open('.\data\template\risqflan_text.txt') as f:
    with open('./data/template/risqflan_text.txt') as f:
        template = Template(f.read())

    name = f'{dict_bbt["model_name"]}Refined'
    print(name)

    attributes =  dict_bbt['attributes']

    name_properties = dict_bbt['name_properties'] 

    actions = dict_bbt['actions']
    actions.append('goBack')#update the actions adding the goBack action

    action_constraints = dict_bbt['action_constraints']

    states = dict_bbt['states']

    quantitative_constraints = dict_bbt['quantitative_constraints']

    transition = final_transitions

    attacks_nodes = dict_bbt['attack_nodes']

    attacks_diagram = dict_bbt['attack_diagram']
    
    countermeasure_nodes = dict_bbt['countermeasure_nodes']
    
    defense_nodes  = dict_bbt['defense_nodes']

    from jinja2 import Environment, FileSystemLoader, select_autoescape


    render = template.render(attacks_nodes = attacks_nodes , attacks_diagram= attacks_diagram, 
                             action_constraints = action_constraints,  actions=actions, states=states, 
                             transitions=transition, name = name, name_properties = name_properties, 
                             attributes = attributes, quantitative_constraints = quantitative_constraints,
                             countermeasure_nodes = countermeasure_nodes, defense_nodes  = defense_nodes )
    with open('./data/refined_BBT/refined_model/'+f"{name}.txt","w") as f:
        f.write(render)

