"""
Statistical Test Decision Tree - Implements the flowchart logic
for guiding users to the correct statistical test.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Callable
from enum import Enum


class TestCategory(Enum):
    ASSOCIATION = "association"
    DIFFERENCE = "difference"
    BOTH = "both"


class VariableType(Enum):
    CONTINUOUS = "continuous"
    CATEGORICAL = "categorical"


class Distribution(Enum):
    NORMAL = "normal"
    NON_NORMAL = "non_normal"
    UNKNOWN = "unknown"


@dataclass
class DecisionNode:
    """Represents a node in the decision tree"""
    id: str
    question: str
    options: List[str]
    next_nodes: Dict[str, str]  # option -> next node id
    is_terminal: bool = False
    recommended_test: Optional[str] = None
    test_explanation: Optional[str] = None


class StatisticalDecisionTree:
    """
    Decision tree for statistical test selection.
    Based on the flowchart: Association vs Difference -> Variable types -> Distribution -> Test
    """
    
    def __init__(self):
        self.nodes = self._build_tree()
        self.current_node_id = "start"
        self.path = []  # Track the path taken
    
    def _build_tree(self) -> Dict[str, DecisionNode]:
        """Build the decision tree based on the flowchart"""
        nodes = {}
        
        # START NODE
        nodes["start"] = DecisionNode(
            id="start",
            question="Are you testing for an **association** (similarity/relationship) or for **differences** between groups?",
            options=["Association", "Difference", "Both"],
            next_nodes={
                "Association": "association_var_type",
                "Difference": "difference_normal",
                "Both": "both_independent"
            }
        )
        
        # ========== ASSOCIATION BRANCH ==========
        nodes["association_var_type"] = DecisionNode(
            id="association_var_type",
            question="Is your Y variable (dependent variable) **categorical** or **continuous**?",
            options=["Continuous", "Categorical"],
            next_nodes={
                "Continuous": "association_continuous",
                "Categorical": "association_categorical"
            }
        )
        
        # Association - Continuous Y
        nodes["association_continuous"] = DecisionNode(
            id="association_continuous",
            question="How many variables are you testing?",
            options=["2 variables", "More than 2 variables"],
            next_nodes={
                "2 variables": "association_normal_check",
                "More than 2 variables": "linear_regression"
            }
        )
        
        nodes["association_normal_check"] = DecisionNode(
            id="association_normal_check",
            question="Is your data **normally distributed**?",
            options=["Yes (Normal)", "No (Non-normal)"],
            next_nodes={
                "Yes (Normal)": "pearson_correlation",
                "No (Non-normal)": "spearman_correlation"
            }
        )
        
        nodes["pearson_correlation"] = DecisionNode(
            id="pearson_correlation",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="pearson_correlation",
            test_explanation="Pearson's correlation coefficient measures the linear relationship between two continuous, normally distributed variables."
        )
        
        nodes["spearman_correlation"] = DecisionNode(
            id="spearman_correlation",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="spearman_correlation",
            test_explanation="Spearman's correlation is a non-parametric measure of rank correlation, suitable for non-normal or ordinal data."
        )
        
        nodes["linear_regression"] = DecisionNode(
            id="linear_regression",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="linear_regression",
            test_explanation="Linear regression models the relationship between a dependent variable and multiple independent variables."
        )
        
        # Association - Categorical Y
        nodes["association_categorical"] = DecisionNode(
            id="association_categorical",
            question="Are the expected frequencies in each cell greater than 5?",
            options=["Yes (≥5)", "No (<5)"],
            next_nodes={
                "Yes (≥5)": "chi_squared_association",
                "No (<5)": "fisher_exact"
            }
        )
        
        nodes["chi_squared_association"] = DecisionNode(
            id="chi_squared_association",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="chi_squared",
            test_explanation="Chi-squared test of independence determines if there's a significant association between two categorical variables."
        )
        
        nodes["fisher_exact"] = DecisionNode(
            id="fisher_exact",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="fisher_exact",
            test_explanation="Fisher's exact test is used when sample sizes are small (expected cell counts < 5) to test association between categorical variables."
        )
        
        # ========== BOTH BRANCH ==========
        nodes["both_independent"] = DecisionNode(
            id="both_independent",
            question="Are your observations **independent** between groups?",
            options=["Yes (Independent)", "No (Dependent/Paired)"],
            next_nodes={
                "Yes (Independent)": "both_linear_check",
                "No (Dependent/Paired)": "glmm"
            }
        )
        
        nodes["both_linear_check"] = DecisionNode(
            id="both_linear_check",
            question="Are the associations **linear** between groups?",
            options=["Yes (Linear)", "No (Non-linear)"],
            next_nodes={
                "Yes (Linear)": "glm",
                "No (Non-linear)": "gam"
            }
        )
        
        nodes["glmm"] = DecisionNode(
            id="glmm",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="glmm",
            test_explanation="Generalized Linear Mixed Models (GLMM) handle non-independent observations with fixed and random effects."
        )
        
        nodes["glm"] = DecisionNode(
            id="glm",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="glm",
            test_explanation="Generalized Linear Models (GLM) extend linear regression to non-normal response distributions."
        )
        
        nodes["gam"] = DecisionNode(
            id="gam",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="gam",
            test_explanation="Generalized Additive Models (GAM) allow for non-linear relationships using smooth functions."
        )
        
        # ========== DIFFERENCE BRANCH ==========
        nodes["difference_normal"] = DecisionNode(
            id="difference_normal",
            question="Is your data **normally distributed**?",
            options=["Yes (Normal)", "No (Non-normal)", "Not sure (check for me)"],
            next_nodes={
                "Yes (Normal)": "difference_groups_normal",
                "No (Non-normal)": "difference_groups_nonnormal",
                "Not sure (check for me)": "difference_groups_normal"  # Will check via code
            }
        )
        
        # Difference - Normal distribution
        nodes["difference_groups_normal"] = DecisionNode(
            id="difference_groups_normal",
            question="How many groups of data are you comparing?",
            options=["1 group (vs. known value)", "2 groups", "More than 2 groups"],
            next_nodes={
                "1 group (vs. known value)": "one_sample_ttest",
                "2 groups": "two_groups_independent_normal",
                "More than 2 groups": "anova"
            }
        )
        
        nodes["one_sample_ttest"] = DecisionNode(
            id="one_sample_ttest",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="one_sample_ttest",
            test_explanation="One-sample t-test compares a sample mean to a known or hypothesized population mean."
        )
        
        nodes["two_groups_independent_normal"] = DecisionNode(
            id="two_groups_independent_normal",
            question="Are the observations **independent** between the two groups?",
            options=["Yes (Independent/Unpaired)", "No (Paired/Matched)"],
            next_nodes={
                "Yes (Independent/Unpaired)": "unpaired_ttest",
                "No (Paired/Matched)": "paired_ttest"
            }
        )
        
        nodes["unpaired_ttest"] = DecisionNode(
            id="unpaired_ttest",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="unpaired_ttest",
            test_explanation="Independent samples t-test (unpaired) compares means of two independent groups."
        )
        
        nodes["paired_ttest"] = DecisionNode(
            id="paired_ttest",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="paired_ttest",
            test_explanation="Paired t-test compares means from the same group at different times or matched subjects."
        )
        
        nodes["anova"] = DecisionNode(
            id="anova",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="anova",
            test_explanation="ANOVA (Analysis of Variance) compares means across 3 or more groups. Use Tukey's HSD for post-hoc pairwise comparisons."
        )
        
        # Difference - Non-normal distribution
        nodes["difference_groups_nonnormal"] = DecisionNode(
            id="difference_groups_nonnormal",
            question="How many groups of data are you comparing?",
            options=["2 groups", "More than 2 groups"],
            next_nodes={
                "2 groups": "two_groups_independent_nonnormal",
                "More than 2 groups": "kruskal_wallis"
            }
        )
        
        nodes["two_groups_independent_nonnormal"] = DecisionNode(
            id="two_groups_independent_nonnormal",
            question="Are the observations **independent** between the two groups?",
            options=["Yes (Independent/Unpaired)", "No (Paired/Matched)"],
            next_nodes={
                "Yes (Independent/Unpaired)": "mann_whitney",
                "No (Paired/Matched)": "wilcoxon"
            }
        )
        
        nodes["mann_whitney"] = DecisionNode(
            id="mann_whitney",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="mann_whitney",
            test_explanation="Mann-Whitney U test (Wilcoxon rank-sum) compares two independent groups when data is non-normal."
        )
        
        nodes["wilcoxon"] = DecisionNode(
            id="wilcoxon",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="wilcoxon_signed_rank",
            test_explanation="Wilcoxon signed-rank test compares paired/matched samples when data is non-normal."
        )
        
        nodes["kruskal_wallis"] = DecisionNode(
            id="kruskal_wallis",
            question="",
            options=[],
            next_nodes={},
            is_terminal=True,
            recommended_test="kruskal_wallis",
            test_explanation="Kruskal-Wallis test is a non-parametric alternative to ANOVA for comparing 3+ groups."
        )
        
        return nodes
    
    def get_current_node(self) -> DecisionNode:
        """Get the current decision node"""
        return self.nodes[self.current_node_id]
    
    def select_option(self, option: str) -> DecisionNode:
        """
        Select an option and move to the next node.
        Returns the next node.
        """
        current = self.get_current_node()
        
        if current.is_terminal:
            return current
        
        # Find matching option (case-insensitive partial match)
        matched_option = None
        for opt in current.options:
            if option.lower() in opt.lower() or opt.lower() in option.lower():
                matched_option = opt
                break
        
        if matched_option and matched_option in current.next_nodes:
            self.path.append((self.current_node_id, matched_option))
            self.current_node_id = current.next_nodes[matched_option]
            return self.get_current_node()
        else:
            # Invalid option, stay at current node
            return current
    
    def reset(self):
        """Reset to the start of the decision tree"""
        self.current_node_id = "start"
        self.path = []
    
    def get_recommendation(self) -> Optional[str]:
        """Get the recommended test if at a terminal node"""
        current = self.get_current_node()
        if current.is_terminal:
            return current.recommended_test
        return None
    
    def get_path_summary(self) -> str:
        """Get a summary of the path taken"""
        if not self.path:
            return "No decisions made yet."
        
        summary = "Your selections:\n"
        for node_id, option in self.path:
            node = self.nodes[node_id]
            summary += f"• {node.question[:50]}... → **{option}**\n"
        return summary


# Singleton instance for the decision tree
decision_tree = StatisticalDecisionTree()
