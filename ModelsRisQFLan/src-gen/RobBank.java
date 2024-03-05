
import atree.core.attacker.*;
import atree.core.attributes.*;
import atree.core.model.*;
import atree.core.nodes.*;
import atree.core.processes.*;
import atree.core.processes.actions.*;
import atree.core.processes.constraints.*;
import atree.core.variables.*;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public class RobBank implements IAtreeModelBuilder {
	
	public RobBank(){
		System.out.println("Model builder instantiated");
	}
	public AtreeModel createModel(){
		
		AtreeModel model = new AtreeModel();		
		
		//////////////////
		/////Variables////
		//////////////////
		AtreeVariable AttackAttempts = model.addVariable("AttackAttempts", new Constant(0.0));
		
		
		/////////////
		////Nodes////
		/////////////
		AttackNode RobBank = new AttackNode("RobBank");
		model.addAttackNodeDefinition(RobBank);
		AttackNode OpenVault = new AttackNode("OpenVault");
		model.addAttackNodeDefinition(OpenVault);
		AttackNode BlowUp = new AttackNode("BlowUp");
		model.addAttackNodeDefinition(BlowUp);
		AttackNode LearnCombo = new AttackNode("LearnCombo");
		model.addAttackNodeDefinition(LearnCombo);
		AttackNode GetToVault = new AttackNode("GetToVault");
		model.addAttackNodeDefinition(GetToVault);
		AttackNode LaserCutter = new AttackNode("LaserCutter");
		model.addAttackNodeDefinition(LaserCutter);
		AttackNode FindCode1 = new AttackNode("FindCode1");
		model.addAttackNodeDefinition(FindCode1);
		AttackNode FindCode2 = new AttackNode("FindCode2");
		model.addAttackNodeDefinition(FindCode2);
		AttackNode FindCode3 = new AttackNode("FindCode3");
		model.addAttackNodeDefinition(FindCode3);
		
		DefenseNode Memo = new DefenseNode("Memo");
		model.addDefenseNodeDefinition(Memo);
		
		CountermeasureNode LockDown = new CountermeasureNode("LockDown");
		model.addCountermeasureNodeDefinition(LockDown,Arrays.asList(BlowUp));
		
		
		/////////////////
		////Relations////
		/////////////////
		LinkedHashMap<String,Set<String>> orRelations = new LinkedHashMap<>(); 
		LinkedHashMap<String,Set<String>> andRelations = new LinkedHashMap<>(); 
		LinkedHashMap<String,Set<String>> knRelations = new LinkedHashMap<>(); 
		LinkedHashMap<String,Set<String>> oandRelations = new LinkedHashMap<>(); 
		LinkedHashMap<String,List<String>> childrenMap = new LinkedHashMap<>();
		LinkedHashMap<String,Integer> knChildren = new LinkedHashMap<>();
		childrenMap.put("set0",Arrays.asList("OpenVault","BlowUp"));
		childrenMap.put("set1",Arrays.asList("LearnCombo","GetToVault"));
		childrenMap.put("set2",Arrays.asList("GetToVault"));
		childrenMap.put("set3",Arrays.asList("FindCode1","FindCode2","FindCode3"));
		knChildren.put("set3",2);
		childrenMap.put("set4",Arrays.asList("LockDown"));
		childrenMap.put("set5",Arrays.asList("LaserCutter"));
		childrenMap.put("set6",Arrays.asList("Memo"));
		orRelations.put("RobBank",new HashSet<>(Arrays.asList("set4","set0")));
		orRelations.put("BlowUp",new HashSet<>(Arrays.asList("set2")));
		orRelations.put("LockDown",new HashSet<>(Arrays.asList("set5")));
		orRelations.put("FindCode2",new HashSet<>(Arrays.asList("set6")));
		andRelations.put("OpenVault",new HashSet<>(Arrays.asList("set1")));
		knRelations.put("LearnCombo",new HashSet<>(Arrays.asList("set3")));
		model.addAllRelations(orRelations,andRelations,knRelations,oandRelations,childrenMap,knChildren);
		
		//////////////////
		////Attributes////
		//////////////////
		AttributeDef Cost = new AttributeDef("Cost");
		model.addAttributeDef(Cost);
		Cost.setNodeValue(LaserCutter,10.0);
		Cost.setNodeValue(BlowUp,90.0);
		Cost.setNodeValue(FindCode1,5.0);
		Cost.setNodeValue(FindCode2,5.0);
		Cost.setNodeValue(FindCode3,5.0);
		
		/////////////////
		////Attackers////
		/////////////////
		Attacker Thief = new Attacker ("Thief");
		model.addAttacker(Thief);
		
		/////////////////////////////
		////Defense Effectiveness////
		/////////////////////////////
		model.setDefenseEffectivenesss(model.getAttackers(), Arrays.asList(FindCode2),Memo,0.5);
		model.setDefenseEffectivenesss(model.getAttackers(), Arrays.asList(RobBank),LockDown,0.3);
		
		///////////////
		////Actions////
		///////////////
		NormalAction tryAction = new NormalAction("tryAction");
		model.addNormalAction(tryAction);
		NormalAction tryGTV = new NormalAction("tryGTV");
		model.addNormalAction(tryGTV);
		NormalAction choose = new NormalAction("choose");
		model.addNormalAction(choose);
		
		//////////////////////////////
		////Attack Detection Rates////
		//////////////////////////////
		BlowUp.setDetectionRate(1.0);
		
		////////////////////////////////
		////Quantitative Constraints////
		////////////////////////////////
		model.addConstraint(new DisequationOfAttributeExpressions(new Attribute(Cost),new Constant(100.0),AttributeExprComparator.LEQ));
		
		//////////////////////////
		////Action Constraints////
		//////////////////////////
		model.addActionConstraint(new ActionRequiresConstraint(choose, new NotConstraintExpr(new BooleanConstraintExpr(new HasNodeConstraint(OpenVault),new HasNodeConstraint(BlowUp),BooleanConnector.OR))));
		
		///////////////////////
		////Attack Diagrams////
		///////////////////////
		ProcessState Start = new ProcessState("Start");
		model.setInitialState(Start);
		ProcessState TryOpenVault = new ProcessState("TryOpenVault");
		ProcessState TryLearnCombo = new ProcessState("TryLearnCombo");
		ProcessState TryFindCode = new ProcessState("TryFindCode");
		ProcessState TryGetToVault = new ProcessState("TryGetToVault");
		ProcessState TryBlowUp = new ProcessState("TryBlowUp");
		ProcessState Complete = new ProcessState("Complete");
		Start.addTransition(new ProcessTransition(2.0,new AddAction(RobBank),Complete,new SideEffect[]{},new AllowedNodeConstraint(RobBank)));
		Start.addTransition(new ProcessTransition(1.0,new FailAction(RobBank),Complete,new SideEffect[]{},new AllowedNodeConstraint(RobBank)));
		Start.addTransition(new ProcessTransition(4.0,tryGTV,TryGetToVault,new SideEffect[]{},new NotConstraintExpr(new HasNodeConstraint(GetToVault))));
		TryGetToVault.addTransition(new ProcessTransition(2.0,new AddAction(GetToVault),Start,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new TrueConstraint()));
		TryGetToVault.addTransition(new ProcessTransition(1.0,new FailAction(GetToVault),Start,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new TrueConstraint()));
		Start.addTransition(new ProcessTransition(4.0,choose,TryOpenVault,new SideEffect[]{},new TrueConstraint()));
		TryOpenVault.addTransition(new ProcessTransition(2.0,new AddAction(OpenVault),Start,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new BooleanConstraintExpr(new HasNodeConstraint(LearnCombo),new HasNodeConstraint(GetToVault),BooleanConnector.AND)));
		TryOpenVault.addTransition(new ProcessTransition(1.0,new FailAction(OpenVault),Start,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new BooleanConstraintExpr(new HasNodeConstraint(LearnCombo),new HasNodeConstraint(GetToVault),BooleanConnector.AND)));
		TryOpenVault.addTransition(new ProcessTransition(2.0,tryAction,Start,new SideEffect[]{},new BooleanConstraintExpr(new HasNodeConstraint(LearnCombo),new NotConstraintExpr(new HasNodeConstraint(GetToVault)),BooleanConnector.AND)));
		TryOpenVault.addTransition(new ProcessTransition(5.0,tryAction,TryLearnCombo,new SideEffect[]{},new NotConstraintExpr(new HasNodeConstraint(LearnCombo))));
		TryLearnCombo.addTransition(new ProcessTransition(5.0,new AddAction(LearnCombo),TryOpenVault,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new TrueConstraint()));
		TryLearnCombo.addTransition(new ProcessTransition(1.0,new FailAction(LearnCombo),TryOpenVault,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new TrueConstraint()));
		TryLearnCombo.addTransition(new ProcessTransition(5.0,tryAction,TryFindCode,new SideEffect[]{},new BooleanConstraintExpr(new NotConstraintExpr(new HasNodeConstraint(FindCode2)),new NotConstraintExpr(new HasNodeConstraint(FindCode3)),BooleanConnector.OR)));
		TryFindCode.addTransition(new ProcessTransition(1.0,new AddAction(FindCode1),TryLearnCombo,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new NotConstraintExpr(new HasNodeConstraint(FindCode1))));
		TryFindCode.addTransition(new ProcessTransition(5.0,new FailAction(FindCode1),TryLearnCombo,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new NotConstraintExpr(new HasNodeConstraint(FindCode1))));
		TryFindCode.addTransition(new ProcessTransition(1.0,new AddAction(FindCode2),TryLearnCombo,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new NotConstraintExpr(new HasNodeConstraint(FindCode2))));
		TryFindCode.addTransition(new ProcessTransition(5.0,new FailAction(FindCode2),TryLearnCombo,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new NotConstraintExpr(new HasNodeConstraint(FindCode2))));
		TryFindCode.addTransition(new ProcessTransition(1.0,new AddAction(FindCode3),TryLearnCombo,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new NotConstraintExpr(new HasNodeConstraint(FindCode3))));
		TryFindCode.addTransition(new ProcessTransition(5.0,new FailAction(FindCode3),TryLearnCombo,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new NotConstraintExpr(new HasNodeConstraint(FindCode3))));
		Start.addTransition(new ProcessTransition(4.0,choose,TryBlowUp,new SideEffect[]{},new TrueConstraint()));
		TryBlowUp.addTransition(new ProcessTransition(2.0,new AddAction(BlowUp),Start,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new TrueConstraint()));
		TryBlowUp.addTransition(new ProcessTransition(1.0,new FailAction(BlowUp),Start,new SideEffect[]{new SideEffect(AttackAttempts,new ArithmeticAttributeExpression(AttackAttempts,new Constant(1.0),ArithmeticOperation.SUM))},new TrueConstraint()));
		
		///////////////////////
		////Initial Attacks////
		///////////////////////
		model.init(Thief,Arrays.asList(FindCode1,LaserCutter));
		
		return model;
	}
}
