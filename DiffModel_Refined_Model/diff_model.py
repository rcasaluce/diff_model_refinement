
"""
This script takes as inputs the CSV of the simulated event logs and the dot file that represents a graphical representation of the procedural part of the RisQFLan model. After pre-processing the event logs, it mines them by applying the heuristic miner algorithm. The process model obtained is then converted into a graph representing a mined RisQFLan model. The script parses the dot file and compares it with the mined RisQFLan model, returning the diff model that highlights the differences between the original model and the simulated one.

Usage:

python diff_model.py -i [CSV] -idot [DOT] -o [NAME] -f [CHOOSE] 


Examples:


python diff_model.py -i input_file.csv -idot input_file.dot -o output_file.pdf 


"""



import argparse
import warnings
warnings.filterwarnings('ignore')
from src.utilities import *



def risqflan(file_csv,file_dot, name_output):
    
    
    """
    Works on any RisQFLan Models.
    
    """
    
    event_log = load_csv_file(file_csv)
    event_log_plus_modes_activity, activities_changed =  pre_processing(event_log, parameter = True)
    heu_net = call_hm_algorithm(event_log_plus_modes_activity, display_pm = False )
    data =  convert_hm_model_to_string(heu_net)
    edges_origin_dest, labels, binary_names = parse_dot_string(data)
    list_unique_activities = save_uniques_acivities(activities_changed, labels)
    edges_origin_dest_labels = match_binary_names_labels(edges_origin_dest,binary_names, labels)
    list_activity_labels = match_origin_destination_activity(edges_origin_dest_labels, list_unique_activities)
    list_for_nodes_edges = list_edges(list_activity_labels)
    check = check_deadlocks(list_for_nodes_edges)
    #if check:
    
    #dict_bbt = extract_everything_from_bbt('RobBank.bbt')
        

    data_old = parse_dot_simulation_model(file_dot)
    edges_origin_dest_old, labels_old = parse_dot_string_2(data_old)
    list_dataframe = match_orig_dest_act_old_RisQFLan(edges_origin_dest_old, labels_old)
    list_for_nodes_edges_old = list_edges_old(list_dataframe)
    dict_old, dict_new = prepare_both_transition_system_RisQFLan(list_for_nodes_edges_old, list_for_nodes_edges)
    dfg_diff, dfg_freq = diff(dict_old,dict_new)
    print('Does the attacker have an initial assets of nodes already gained?')
    request = str(input('Yes or No? Type y or n:  '))
    if request.lower() == 'yes' or request.lower() == 'y':
        initial_assets = str(input('Type the names of the nodes already gained by the attacker separated by a comma:  '))
    
        #initial_assets = [item.strip() for item in initial_assets.split(',')]
        initial_assets = [item.strip().lower() for item in initial_assets.split(',')]



        print('initial_assets', initial_assets)
    else:
          initial_assets =[]
    draw_diff_initial(dfg_diff, name_output, initial_assets).view()
    #draw_diff_initial(dfg_diff, name_output).view()






if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('-i', '--inputcsv', type=str, required=True, help='Input CSV file - simulated event logs saved from RisQFLan')
    parser.add_argument('-idot', '--inputdot', type=str, required=True, help='Input DOT file - the graphical representation of the procedural part of the RisQFLan')
    
    parser.add_argument('-o', '--output', type=str, required=True, help='Output NAME - Diff model between the graphical representation of the procedural part of the RisQFLan model and the mined PM model')


    args = parser.parse_args()

    
    risqflan(args.inputcsv,args.inputdot, args.output)
    



