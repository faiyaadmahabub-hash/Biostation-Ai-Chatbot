"""
Comprehensive Keyword Dictionary for Intent Detection
Contains 500+ patterns for bioscience and statistics domains.
"""

from typing import Dict, List, Set

# Intent categories with comprehensive keyword patterns
# Structure: intent_id -> { 'primary': high-confidence keywords, 
#                           'secondary': context keywords,
#                           'phrases': multi-word patterns }

INTENT_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    
    # ============ COMPARISON TESTS ============
    'compare_groups': {
        'primary': [
            # T-tests
            't-test', 'ttest', 't test', 'student t', 'welch',
            # ANOVA
            'anova', 'aov', 'analysis of variance', 'f-test', 'f test',
            # General comparison
            'compare', 'comparison', 'difference', 'differ', 'different',
            # Non-parametric
            'mann-whitney', 'mann whitney', 'wilcoxon', 'kruskal', 'kruskal-wallis',
        ],
        'secondary': [
            'between', 'groups', 'means', 'averages', 'treatment', 'control',
            'vs', 'versus', 'against', 'two groups', 'multiple groups',
            'paired', 'unpaired', 'independent', 'dependent',
            'significant', 'significance', 'statistical', 'p-value', 'pvalue',
        ],
        'phrases': [
            'is there a difference',
            'are they different',
            'compare means',
            'significant difference',
            'test for difference',
            'group comparison',
            'treatment effect',
            'before and after',
            'pre and post',
            'experimental vs control',
        ],
    },
    
    # ============ CORRELATION ============
    'correlation': {
        'primary': [
            'correlation', 'correlate', 'correlated', 'correlating',
            'pearson', 'spearman', 'kendall',
            'relationship', 'relate', 'related', 'association', 'associate',
            'covariance', 'covariate',
        ],
        'secondary': [
            'between', 'variables', 'linear', 'monotonic',
            'positive', 'negative', 'strength', 'direction',
            'scatter', 'scatterplot', 'trend',
            'r-value', 'rho', 'coefficient',
        ],
        'phrases': [
            'is there a relationship',
            'are they related',
            'correlation between',
            'how strong',
            'linear relationship',
            'association between',
            'covary',
            'move together',
        ],
    },

    # ============ CORRELATION MATRIX ============
    'correlation_matrix': {
        'primary': [
            'correlation matrix', 'correlation heatmap', 'heatmap',
            'correlogram', 'corr matrix', 'cor matrix',
            'all correlations', 'pairwise correlations',
            'correlation plot', 'correlation table',
        ],
        'secondary': [
            'numeric', 'all variables', 'numeric columns',
            'matrix', 'overview', 'summary',
            'p-value', 'significance', 'stars',
        ],
        'phrases': [
            'show correlation matrix',
            'correlation matrix heatmap',
            'generate correlation matrix',
            'show all correlations',
            'correlations between all variables',
            'correlation heatmap',
            'pairwise correlation matrix',
            'create correlation matrix',
            'plot correlation matrix',
            'visualize correlations',
            'correlation overview',
        ],
    },
    
    # ============ REGRESSION ============
    'regression': {
        'primary': [
            'regression', 'regress', 'predict', 'prediction', 'predictive',
            'linear model', 'lm', 'glm', 'generalized linear',
            'logistic', 'poisson', 'binomial',
            'fit', 'fitting', 'model',
        ],
        'secondary': [
            'outcome', 'response', 'dependent', 'independent',
            'predictor', 'covariate', 'explanatory',
            'coefficient', 'slope', 'intercept',
            'r-squared', 'rsquared', 'r2', 'adjusted',
            'residual', 'fitted',
        ],
        'phrases': [
            'predict outcome',
            'build a model',
            'linear regression',
            'logistic regression',
            'multiple regression',
            'effect of x on y',
            'what predicts',
            'regression analysis',
        ],
    },
    
    # ============ DESCRIPTIVE STATISTICS ============
    'descriptive_stats': {
        'primary': [
            'mean', 'average', 'median', 'mode',
            'standard deviation', 'std', 'sd', 'stdev',
            'variance', 'var',
            'range', 'min', 'max', 'minimum', 'maximum',
            'summary', 'summarize', 'summarise', 'describe', 'descriptive',
            'distribution', 'frequency', 'histogram',
            'quartile', 'percentile', 'iqr', 'interquartile',
        ],
        'secondary': [
            'statistics', 'stats', 'calculate', 'compute',
            'central tendency', 'spread', 'dispersion',
            'skewness', 'kurtosis', 'normal', 'normality',
        ],
        'phrases': [
            'descriptive statistics',
            'summary statistics',
            'calculate mean',
            'find average',
            'what is the mean',
            'measure of central',
            'standard deviation of',
            'describe the data',
            'data summary',
        ],
    },
    
    # ============ CHI-SQUARED / CATEGORICAL ============
    'categorical_test': {
        'primary': [
            'chi-square', 'chi-squared', 'chi square', 'chisq', 'χ2',
            'fisher', "fisher's exact", 'fishers exact',
            'contingency', 'crosstab', 'cross-tabulation',
            'categorical', 'frequency', 'count',
            'proportion', 'odds ratio', 'odds',
        ],
        'secondary': [
            'table', 'independence', 'association',
            'observed', 'expected', 'cells',
            'nominal', 'ordinal', 'binary',
        ],
        'phrases': [
            'chi-squared test',
            'test of independence',
            'categorical variables',
            'contingency table',
            "fisher's exact test",
            'compare proportions',
            'frequency analysis',
        ],
    },
    
    # ============ NORMALITY TESTING ============
    'normality_test': {
        'primary': [
            'normality', 'normal distribution', 'shapiro', 'shapiro-wilk',
            'kolmogorov', 'ks-test', 'anderson', 'anderson-darling',
            'qq', 'q-q', 'qqplot',
        ],
        'secondary': [
            'assumption', 'check', 'test', 'verify',
            'gaussian', 'bell curve', 'symmetric',
            'skew', 'skewness',
        ],
        'phrases': [
            'is it normal',
            'check normality',
            'test for normality',
            'normally distributed',
            'shapiro-wilk test',
            'qq plot',
            'normal assumption',
        ],
    },
    
    # ============ EXPLANATION REQUESTS ============
    'explain_concept': {
        'primary': [
            'explain', 'explanation', 'what is', 'what are',
            'tell me about', 'describe', 'define', 'definition',
            'how does', 'how do', 'why', 'when to use',
            'understand', 'help me understand', 'clarify',
            'meaning', 'means', 'concept',
        ],
        'secondary': [
            'learn', 'teach', 'tutorial', 'guide',
            'example', 'instance', 'case',
            'difference between', 'versus',
        ],
        'phrases': [
            'what is a t-test',
            'explain anova',
            'what does p-value mean',
            'when should i use',
            'difference between',
            'how to interpret',
            'tell me about',
            'can you explain',
            'i dont understand',
            "i don't understand",
            'help me with',
        ],
    },
    
    # ============ TEST SELECTION ============
    'test_selection': {
        'primary': [
            'which test', 'what test', 'choose', 'select', 'recommend',
            'appropriate', 'suitable', 'best', 'right test',
            'should i use', 'help me choose', 'guide',
        ],
        'secondary': [
            'statistical test', 'analysis', 'method',
            'my data', 'for my',
        ],
        'phrases': [
            'which test should i use',
            'what test is appropriate',
            'help me choose a test',
            'recommend a test',
            'guide me through',
            'best test for',
            'which analysis',
            'what should i do',
        ],
    },
    
    # ============ CODE GENERATION ============
    'code_generation': {
        'primary': [
            'generate', 'create', 'write', 'give me', 'show me',
            'code', 'script', 'syntax', 'command',
            'r code', 'r script',
        ],
        'secondary': [
            'run', 'execute', 'perform', 'conduct',
            'analysis', 'test', 'statistical',
        ],
        'phrases': [
            'generate code for',
            'give me r code',
            'write code for',
            'show me how to code',
            'r code for',
            'create a script',
            'code to perform',
            'how to run',
            'code example',
        ],
    },
    
    # ============ ERROR DEBUGGING ============
    'debug_error': {
        'primary': [
            'error', 'bug', 'problem', 'issue', 'wrong',
            'fix', 'debug', 'troubleshoot', 'solve',
            'not working', 'doesnt work', "doesn't work", 'failed',
            'help', 'stuck',
        ],
        'secondary': [
            'r error', 'code error', 'warning', 'message',
            'exception', 'crash', 'unexpected',
        ],
        'phrases': [
            'getting an error',
            'my code is not working',
            'what does this error mean',
            'how to fix',
            'help me debug',
            'something went wrong',
            'error message',
            'keeps failing',
        ],
    },
    
    # ============ DATA OPERATIONS ============
    'data_operation': {
        'primary': [
            'load', 'import', 'read', 'open',
            'clean', 'cleaning', 'preprocess', 'preprocessing',
            'filter', 'subset', 'select', 'remove', 'delete',
            'transform', 'convert', 'reshape',
            'merge', 'join', 'combine', 'bind',
            'missing', 'na', 'null', 'empty',
        ],
        'secondary': [
            'data', 'dataset', 'file', 'csv', 'excel',
            'column', 'row', 'variable', 'observation',
        ],
        'phrases': [
            'load my data',
            'read csv',
            'clean my data',
            'handle missing values',
            'remove na',
            'filter data',
            'subset by',
            'merge datasets',
        ],
    },
    
    # ============ VISUALIZATION ============
    'visualization': {
        'primary': [
            'plot', 'graph', 'chart', 'figure', 'visual', 'visualize', 'visualise',
            'histogram', 'boxplot', 'box plot', 'scatter', 'scatterplot',
            'bar', 'barplot', 'bar chart', 'line', 'lineplot',
            'heatmap', 'density', 'violin',
        ],
        'secondary': [
            'show', 'display', 'view', 'see',
            'color', 'legend', 'axis', 'title', 'label',
            'ggplot', 'base r', 'plotly',
        ],
        'phrases': [
            'create a plot',
            'make a graph',
            'visualize results',
            'show me a chart',
            'plot the data',
            'boxplot of',
            'histogram of',
            'scatter plot',
        ],
    },
    
    # ============ POWER & SAMPLE SIZE ============
    'power_analysis': {
        'primary': [
            'power', 'sample size', 'effect size',
            'power analysis', 'power calculation',
            'how many', 'minimum sample', 'required sample',
        ],
        'secondary': [
            'n', 'subjects', 'participants', 'observations',
            'detect', 'alpha', 'beta', 'type i', 'type ii',
        ],
        'phrases': [
            'sample size calculation',
            'how many subjects do i need',
            'power analysis',
            'effect size calculation',
            'minimum sample size',
            'statistical power',
        ],
    },
    
    # ============ POST-HOC TESTS & MULTIPLE COMPARISON CORRECTIONS ============
    'post_hoc': {
        'primary': [
            'post-hoc', 'post hoc', 'posthoc', 'pairwise',
            'tukey', 'bonferroni', 'scheffe', 'dunnett', 'dunn',
            'multiple comparisons', 'correction', 'corrections',
            'holm', 'holm-bonferroni', 'fdr', 'benjamini', 'hochberg',
            'benjamini-hochberg', 'false discovery', 'familywise',
            'p-value adjustment', 'adjust p-value', 'adjusted p',
            'multiple testing', 'type i error', 'false positive',
        ],
        'secondary': [
            'follow-up', 'followup', 'which groups differ',
            'adjustment', 'family-wise', 'fwer',
            'control error', 'alpha', 'significance level',
            'conservative', 'exploratory', 'confirmatory',
        ],
        'phrases': [
            'post hoc test',
            'which groups are different',
            'pairwise comparisons',
            'tukey test',
            'bonferroni correction',
            'holm correction',
            'fdr correction',
            'multiple comparison correction',
            'which correction should i use',
            'correct for multiple testing',
            'adjust for multiple comparisons',
            'control false discovery rate',
            'familywise error rate',
            'too many comparisons',
            'inflated type i error',
        ],
    },
    
    # ============ SURVIVAL ANALYSIS ============
    'survival_analysis': {
        'primary': [
            'survival', 'kaplan', 'kaplan-meier', 'cox',
            'hazard', 'time-to-event', 'censored', 'censoring',
            'log-rank', 'logrank',
        ],
        'secondary': [
            'death', 'failure', 'event', 'time',
            'curve', 'probability', 'risk',
        ],
        'phrases': [
            'survival analysis',
            'kaplan meier curve',
            'cox regression',
            'time to event',
            'survival probability',
            'hazard ratio',
        ],
    },
}

# Additional bioscience-specific vocabulary
BIOSCIENCE_TERMS = {
    # Experiment types
    'experiments': [
        'experiment', 'study', 'trial', 'assay', 'test',
        'in vitro', 'in vivo', 'ex vivo',
        'control', 'treatment', 'intervention',
        'replicate', 'repeat', 'duplicate', 'triplicate',
    ],
    
    # Organisms and samples
    'samples': [
        'sample', 'specimen', 'subject', 'patient', 'participant',
        'cell', 'tissue', 'organ', 'organism',
        'mouse', 'mice', 'rat', 'human', 'animal', 'plant',
        'bacteria', 'virus', 'yeast', 'culture',
        'gene', 'protein', 'dna', 'rna', 'mrna',
    ],
    
    # Measurements
    'measurements': [
        'concentration', 'absorbance', 'fluorescence', 'luminescence',
        'expression', 'level', 'activity', 'viability',
        'growth', 'proliferation', 'apoptosis', 'death',
        'weight', 'height', 'length', 'size', 'diameter',
        'ph', 'temperature', 'time', 'dose', 'response',
    ],
    
    # Analysis types
    'analysis_types': [
        'western blot', 'pcr', 'qpcr', 'rt-pcr',
        'elisa', 'facs', 'flow cytometry',
        'sequencing', 'rna-seq', 'chip-seq',
        'microscopy', 'imaging',
    ],
}

# Common action verbs for intent detection
ACTION_VERBS = [
    'do', 'run', 'perform', 'conduct', 'execute',
    'analyze', 'analyse', 'test', 'check', 'verify',
    'calculate', 'compute', 'find', 'get', 'show',
    'compare', 'measure', 'assess', 'evaluate',
]

# Negation words (to avoid false positives)
NEGATION_WORDS = ['not', "don't", 'dont', 'no', 'never', 'without', 'cant', "can't"]


class StaticKeywordMatcher:
    """Fast keyword-based intent detection"""
    
    def __init__(self):
        self.intent_keywords = INTENT_KEYWORDS
        self.bioscience_terms = BIOSCIENCE_TERMS
        self.action_verbs = set(ACTION_VERBS)
        
        # Build reverse lookup for faster matching
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        """Build reverse index: keyword -> intent"""
        self.keyword_to_intent: Dict[str, List[tuple]] = {}
        
        for intent, categories in self.intent_keywords.items():
            # Primary keywords get high weight
            for kw in categories.get('primary', []):
                if kw not in self.keyword_to_intent:
                    self.keyword_to_intent[kw] = []
                self.keyword_to_intent[kw].append((intent, 1.0))
            
            # Secondary keywords get medium weight
            for kw in categories.get('secondary', []):
                if kw not in self.keyword_to_intent:
                    self.keyword_to_intent[kw] = []
                self.keyword_to_intent[kw].append((intent, 0.5))
            
            # Phrases get highest weight
            for phrase in categories.get('phrases', []):
                if phrase not in self.keyword_to_intent:
                    self.keyword_to_intent[phrase] = []
                self.keyword_to_intent[phrase].append((intent, 1.5))
    
    def match(self, query: str) -> dict:
        """
        Match query against keywords.
        Returns: {'intent': str, 'confidence': float, 'matches': list}
        """
        query_lower = query.lower().strip()
        intent_scores: Dict[str, float] = {}
        matched_keywords: Dict[str, List[str]] = {}
        
        # Check for phrase matches first (highest priority)
        for intent, categories in self.intent_keywords.items():
            for phrase in categories.get('phrases', []):
                if phrase in query_lower:
                    if intent not in intent_scores:
                        intent_scores[intent] = 0
                        matched_keywords[intent] = []
                    intent_scores[intent] += 1.5
                    matched_keywords[intent].append(f"phrase:{phrase}")
        
        # Check for primary keywords
        for intent, categories in self.intent_keywords.items():
            for kw in categories.get('primary', []):
                if kw in query_lower:
                    if intent not in intent_scores:
                        intent_scores[intent] = 0
                        matched_keywords[intent] = []
                    intent_scores[intent] += 1.0
                    matched_keywords[intent].append(f"primary:{kw}")
        
        # Check for secondary keywords (only boost existing intents)
        for intent, categories in self.intent_keywords.items():
            if intent in intent_scores:  # Only boost if already matched
                for kw in categories.get('secondary', []):
                    if kw in query_lower:
                        intent_scores[intent] += 0.3
                        matched_keywords[intent].append(f"secondary:{kw}")
        
        # Find best intent
        if not intent_scores:
            return {
                'intent': None,
                'confidence': 0.0,
                'matches': [],
                'method': 'keyword_no_match'
            }
        
        best_intent = max(intent_scores, key=intent_scores.get)
        best_score = intent_scores[best_intent]
        
        # Calculate confidence (normalize by max possible score)
        # Confidence thresholds: >1.5 = high, >1.0 = medium, >0.5 = low
        confidence = min(best_score / 2.0, 1.0)  # Normalize to 0-1
        
        return {
            'intent': best_intent,
            'confidence': confidence,
            'matches': matched_keywords.get(best_intent, []),
            'method': 'keyword_match',
            'all_scores': intent_scores
        }
    
    def get_all_keywords(self) -> Set[str]:
        """Return all keywords for vocabulary expansion"""
        all_kw = set()
        for intent, categories in self.intent_keywords.items():
            all_kw.update(categories.get('primary', []))
            all_kw.update(categories.get('secondary', []))
            all_kw.update(categories.get('phrases', []))
        return all_kw


# Singleton instance
_matcher = None

def get_keyword_matcher() -> StaticKeywordMatcher:
    """Get or create keyword matcher singleton"""
    global _matcher
    if _matcher is None:
        _matcher = StaticKeywordMatcher()
    return _matcher
