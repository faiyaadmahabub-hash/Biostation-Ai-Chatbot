"""
Dataset Registry - Metadata for built-in datasets

Contains comprehensive information about each dataset including:
- Description and source
- Variable information
- Suggested analyses
- Learning objectives
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class VariableType(Enum):
    """Types of variables in datasets"""
    NUMERIC = "numeric"
    CATEGORICAL = "categorical"
    ORDINAL = "ordinal"
    BINARY = "binary"


class AnalysisType(Enum):
    """Types of statistical analyses"""
    TTEST = "t-test"
    ANOVA = "anova"
    TWO_WAY_ANOVA = "two_way_anova"
    CORRELATION = "correlation"
    REGRESSION = "regression"
    CHI_SQUARED = "chi_squared"
    NONPARAMETRIC = "nonparametric"
    DESCRIPTIVE = "descriptive"


@dataclass
class Variable:
    """Information about a dataset variable"""
    name: str
    type: VariableType
    description: str
    units: Optional[str] = None
    levels: Optional[List[str]] = None  # For categorical variables


@dataclass
class SuggestedAnalysis:
    """A suggested analysis for a dataset"""
    type: AnalysisType
    title: str
    description: str
    variables: Dict[str, str]  # Maps role to variable name (e.g., {"outcome": "Sepal.Length", "group": "Species"})
    query_example: str  # Example query user could type


@dataclass
class DatasetInfo:
    """Complete information about a built-in dataset"""
    id: str
    name: str
    description: str
    source: str
    n_rows: int
    n_cols: int
    variables: List[Variable]
    suggested_analyses: List[SuggestedAnalysis]
    tags: List[str]
    difficulty: str  # "beginner", "intermediate", "advanced"
    learning_objectives: List[str]


# ============ DATASET DEFINITIONS ============

BUILTIN_DATASETS: Dict[str, DatasetInfo] = {

    "iris": DatasetInfo(
        id="iris",
        name="Iris Flower Dataset",
        description="Famous dataset containing measurements of iris flowers from three species. "
                    "Collected by Edgar Anderson and used by R.A. Fisher to demonstrate linear discriminant analysis.",
        source="Fisher, R.A. (1936) The use of multiple measurements in taxonomic problems.",
        n_rows=150,
        n_cols=5,
        variables=[
            Variable("Sepal.Length", VariableType.NUMERIC, "Length of sepal in cm", "cm"),
            Variable("Sepal.Width", VariableType.NUMERIC, "Width of sepal in cm", "cm"),
            Variable("Petal.Length", VariableType.NUMERIC, "Length of petal in cm", "cm"),
            Variable("Petal.Width", VariableType.NUMERIC, "Width of petal in cm", "cm"),
            Variable("Species", VariableType.CATEGORICAL, "Species of iris flower",
                    levels=["setosa", "versicolor", "virginica"]),
        ],
        suggested_analyses=[
            SuggestedAnalysis(
                type=AnalysisType.ANOVA,
                title="Compare Sepal Length Across Species",
                description="Test if sepal length differs significantly between the three iris species.",
                variables={"outcome": "Sepal.Length", "group": "Species"},
                query_example="Compare sepal length between species using ANOVA"
            ),
            SuggestedAnalysis(
                type=AnalysisType.CORRELATION,
                title="Petal Length vs Petal Width Correlation",
                description="Examine the relationship between petal dimensions.",
                variables={"x": "Petal.Length", "y": "Petal.Width"},
                query_example="Is there a correlation between petal length and width?"
            ),
            SuggestedAnalysis(
                type=AnalysisType.DESCRIPTIVE,
                title="Descriptive Statistics by Species",
                description="Get summary statistics for all measurements grouped by species.",
                variables={},
                query_example="Show descriptive statistics for the iris dataset"
            ),
        ],
        tags=["classification", "multivariate", "biology", "flowers"],
        difficulty="beginner",
        learning_objectives=[
            "Practice ANOVA for comparing multiple groups",
            "Explore correlation between continuous variables",
            "Learn to visualize group differences with boxplots",
        ]
    ),

    "mtcars": DatasetInfo(
        id="mtcars",
        name="Motor Trend Car Road Tests",
        description="Data from the 1974 Motor Trend US magazine comprising fuel consumption and "
                    "10 aspects of automobile design and performance for 32 automobiles.",
        source="Henderson and Velleman (1981), Building multiple regression models interactively.",
        n_rows=32,
        n_cols=11,
        variables=[
            Variable("mpg", VariableType.NUMERIC, "Miles per gallon (fuel efficiency)", "mpg"),
            Variable("cyl", VariableType.CATEGORICAL, "Number of cylinders", levels=["4", "6", "8"]),
            Variable("disp", VariableType.NUMERIC, "Displacement", "cu.in."),
            Variable("hp", VariableType.NUMERIC, "Gross horsepower", "hp"),
            Variable("drat", VariableType.NUMERIC, "Rear axle ratio"),
            Variable("wt", VariableType.NUMERIC, "Weight", "1000 lbs"),
            Variable("qsec", VariableType.NUMERIC, "1/4 mile time", "seconds"),
            Variable("vs", VariableType.BINARY, "Engine shape (0=V-shaped, 1=straight)", levels=["0", "1"]),
            Variable("am", VariableType.BINARY, "Transmission (0=automatic, 1=manual)", levels=["0", "1"]),
            Variable("gear", VariableType.CATEGORICAL, "Number of forward gears", levels=["3", "4", "5"]),
            Variable("carb", VariableType.NUMERIC, "Number of carburetors"),
        ],
        suggested_analyses=[
            SuggestedAnalysis(
                type=AnalysisType.TTEST,
                title="MPG: Automatic vs Manual Transmission",
                description="Compare fuel efficiency between automatic and manual transmission cars.",
                variables={"outcome": "mpg", "group": "am"},
                query_example="Is there a difference in mpg between automatic and manual cars?"
            ),
            SuggestedAnalysis(
                type=AnalysisType.REGRESSION,
                title="Predict MPG from Weight and Horsepower",
                description="Build a regression model to predict fuel efficiency.",
                variables={"outcome": "mpg", "predictors": "wt + hp"},
                query_example="Can we predict mpg from weight and horsepower?"
            ),
            SuggestedAnalysis(
                type=AnalysisType.ANOVA,
                title="MPG Across Cylinder Groups",
                description="Compare fuel efficiency across 4, 6, and 8 cylinder cars.",
                variables={"outcome": "mpg", "group": "cyl"},
                query_example="Compare mpg between cars with different cylinder counts"
            ),
            SuggestedAnalysis(
                type=AnalysisType.CORRELATION,
                title="Correlation Matrix",
                description="Explore relationships between all numeric variables.",
                variables={},
                query_example="Show correlation matrix for mtcars"
            ),
        ],
        tags=["regression", "automotive", "engineering", "multivariate"],
        difficulty="intermediate",
        learning_objectives=[
            "Practice multiple regression with multiple predictors",
            "Learn to compare groups with t-tests",
            "Understand correlation between variables",
            "Handle both numeric and categorical predictors",
        ]
    ),

    "toothgrowth": DatasetInfo(
        id="toothgrowth",
        name="Tooth Growth in Guinea Pigs",
        description="Effect of Vitamin C on tooth growth in guinea pigs. Each animal received one of "
                    "three dose levels of vitamin C by one of two delivery methods.",
        source="C. I. Bliss (1952). The Statistics of Bioassay.",
        n_rows=60,
        n_cols=3,
        variables=[
            Variable("len", VariableType.NUMERIC, "Tooth length (odontoblast length)", "microns"),
            Variable("supp", VariableType.CATEGORICAL, "Supplement type", levels=["VC", "OJ"]),
            Variable("dose", VariableType.ORDINAL, "Dose of vitamin C", "mg/day", levels=["0.5", "1", "2"]),
        ],
        suggested_analyses=[
            SuggestedAnalysis(
                type=AnalysisType.TWO_WAY_ANOVA,
                title="Two-Way ANOVA: Supplement x Dose",
                description="Analyze the effects of supplement type and dose on tooth growth, including interaction.",
                variables={"outcome": "len", "factor1": "supp", "factor2": "dose"},
                query_example="Perform two-way ANOVA on tooth growth with supp and dose"
            ),
            SuggestedAnalysis(
                type=AnalysisType.TTEST,
                title="Compare Supplement Types",
                description="Compare tooth growth between orange juice (OJ) and ascorbic acid (VC).",
                variables={"outcome": "len", "group": "supp"},
                query_example="Is orange juice better than vitamin C for tooth growth?"
            ),
            SuggestedAnalysis(
                type=AnalysisType.ANOVA,
                title="Effect of Dose Level",
                description="Test if tooth growth increases with vitamin C dose.",
                variables={"outcome": "len", "group": "dose"},
                query_example="Does tooth growth differ by vitamin C dose?"
            ),
        ],
        tags=["factorial", "biology", "experiment", "dose-response"],
        difficulty="intermediate",
        learning_objectives=[
            "Practice two-way ANOVA with interaction",
            "Understand factorial experimental designs",
            "Learn post-hoc comparisons",
        ]
    ),

    "plantgrowth": DatasetInfo(
        id="plantgrowth",
        name="Plant Growth Experiment",
        description="Results from an experiment comparing yields obtained under a control and two "
                    "different treatment conditions.",
        source="Dobson, A. J. (1983) An Introduction to Statistical Modelling.",
        n_rows=30,
        n_cols=2,
        variables=[
            Variable("weight", VariableType.NUMERIC, "Dried weight of plants", "g"),
            Variable("group", VariableType.CATEGORICAL, "Treatment group",
                    levels=["ctrl", "trt1", "trt2"]),
        ],
        suggested_analyses=[
            SuggestedAnalysis(
                type=AnalysisType.ANOVA,
                title="Compare Treatment Effects",
                description="Test if plant growth differs between control and treatment groups.",
                variables={"outcome": "weight", "group": "group"},
                query_example="Compare plant weight between treatment groups using ANOVA"
            ),
            SuggestedAnalysis(
                type=AnalysisType.NONPARAMETRIC,
                title="Kruskal-Wallis Test",
                description="Non-parametric alternative if normality assumption is violated.",
                variables={"outcome": "weight", "group": "group"},
                query_example="Run Kruskal-Wallis test on plant growth data"
            ),
        ],
        tags=["anova", "biology", "experiment", "agriculture"],
        difficulty="beginner",
        learning_objectives=[
            "Learn one-way ANOVA basics",
            "Practice post-hoc testing (Tukey HSD)",
            "Understand experimental design",
        ]
    ),

    "chickweight": DatasetInfo(
        id="chickweight",
        name="Chick Weight Over Time",
        description="Weight of chicks measured over time on different diets. A longitudinal study "
                    "tracking growth from birth to 21 days.",
        source="Crowder, M. and Hand, D. (1990), Analysis of Repeated Measures.",
        n_rows=578,
        n_cols=4,
        variables=[
            Variable("weight", VariableType.NUMERIC, "Body weight of chick", "grams"),
            Variable("Time", VariableType.NUMERIC, "Days since birth", "days"),
            Variable("Chick", VariableType.CATEGORICAL, "Unique chick identifier"),
            Variable("Diet", VariableType.CATEGORICAL, "Diet type", levels=["1", "2", "3", "4"]),
        ],
        suggested_analyses=[
            SuggestedAnalysis(
                type=AnalysisType.ANOVA,
                title="Compare Diets at Day 21",
                description="Compare final weights across different diet groups.",
                variables={"outcome": "weight", "group": "Diet"},
                query_example="Compare chick weights between diets at day 21"
            ),
            SuggestedAnalysis(
                type=AnalysisType.REGRESSION,
                title="Growth Rate Analysis",
                description="Model weight as a function of time.",
                variables={"outcome": "weight", "predictor": "Time"},
                query_example="How does chick weight change over time?"
            ),
        ],
        tags=["longitudinal", "repeated-measures", "biology", "nutrition"],
        difficulty="intermediate",
        learning_objectives=[
            "Work with longitudinal/repeated measures data",
            "Compare groups over time",
            "Understand growth curve analysis",
        ]
    ),

    "sleep": DatasetInfo(
        id="sleep",
        name="Student Sleep Data",
        description="Data showing the effect of two soporific drugs on 10 patients. Each patient "
                    "received both drugs, making this a paired design.",
        source="Cushny, A. R. and Peebles, A. R. (1905) The action of optical isomers.",
        n_rows=20,
        n_cols=3,
        variables=[
            Variable("extra", VariableType.NUMERIC, "Increase in hours of sleep", "hours"),
            Variable("group", VariableType.CATEGORICAL, "Drug type", levels=["1", "2"]),
            Variable("ID", VariableType.CATEGORICAL, "Patient identifier"),
        ],
        suggested_analyses=[
            SuggestedAnalysis(
                type=AnalysisType.TTEST,
                title="Paired T-Test: Drug 1 vs Drug 2",
                description="Compare the effectiveness of two sleep drugs using paired design.",
                variables={"outcome": "extra", "group": "group", "paired": "ID"},
                query_example="Compare the two sleep drugs using a paired t-test"
            ),
            SuggestedAnalysis(
                type=AnalysisType.NONPARAMETRIC,
                title="Wilcoxon Signed-Rank Test",
                description="Non-parametric alternative for paired comparison.",
                variables={"outcome": "extra", "group": "group"},
                query_example="Run Wilcoxon test to compare sleep drugs"
            ),
        ],
        tags=["paired", "medical", "clinical-trial", "before-after"],
        difficulty="beginner",
        learning_objectives=[
            "Understand paired vs unpaired designs",
            "Practice paired t-test",
            "Learn when to use non-parametric alternatives",
        ]
    ),

    "airquality": DatasetInfo(
        id="airquality",
        name="New York Air Quality",
        description="Daily air quality measurements in New York from May to September 1973. "
                    "Contains missing values, making it useful for learning data cleaning.",
        source="New York State Department of Conservation and National Weather Service.",
        n_rows=153,
        n_cols=6,
        variables=[
            Variable("Ozone", VariableType.NUMERIC, "Ozone concentration", "ppb"),
            Variable("Solar.R", VariableType.NUMERIC, "Solar radiation", "lang"),
            Variable("Wind", VariableType.NUMERIC, "Wind speed", "mph"),
            Variable("Temp", VariableType.NUMERIC, "Temperature", "F"),
            Variable("Month", VariableType.CATEGORICAL, "Month (5-9)", levels=["5", "6", "7", "8", "9"]),
            Variable("Day", VariableType.NUMERIC, "Day of month"),
        ],
        suggested_analyses=[
            SuggestedAnalysis(
                type=AnalysisType.CORRELATION,
                title="Temperature and Ozone Correlation",
                description="Examine relationship between temperature and ozone levels.",
                variables={"x": "Temp", "y": "Ozone"},
                query_example="Is there a correlation between temperature and ozone?"
            ),
            SuggestedAnalysis(
                type=AnalysisType.REGRESSION,
                title="Predict Ozone Levels",
                description="Build a model to predict ozone from weather variables.",
                variables={"outcome": "Ozone", "predictors": "Solar.R + Wind + Temp"},
                query_example="Predict ozone levels from solar radiation, wind, and temperature"
            ),
            SuggestedAnalysis(
                type=AnalysisType.ANOVA,
                title="Ozone Levels by Month",
                description="Compare ozone levels across different months.",
                variables={"outcome": "Ozone", "group": "Month"},
                query_example="Does ozone level differ by month?"
            ),
        ],
        tags=["environmental", "time-series", "missing-data", "regression"],
        difficulty="intermediate",
        learning_objectives=[
            "Handle missing values in real data",
            "Practice multiple regression",
            "Understand environmental data analysis",
        ]
    ),

    "faithful": DatasetInfo(
        id="faithful",
        name="Old Faithful Geyser Data",
        description="Waiting time between eruptions and duration of eruptions for the Old Faithful "
                    "geyser in Yellowstone National Park.",
        source="Azzalini, A. and Bowman, A. W. (1990).",
        n_rows=272,
        n_cols=2,
        variables=[
            Variable("eruptions", VariableType.NUMERIC, "Eruption duration", "minutes"),
            Variable("waiting", VariableType.NUMERIC, "Waiting time to next eruption", "minutes"),
        ],
        suggested_analyses=[
            SuggestedAnalysis(
                type=AnalysisType.CORRELATION,
                title="Eruption Duration vs Waiting Time",
                description="Examine if longer eruptions are followed by longer waiting times.",
                variables={"x": "eruptions", "y": "waiting"},
                query_example="Is there a correlation between eruption duration and waiting time?"
            ),
            SuggestedAnalysis(
                type=AnalysisType.REGRESSION,
                title="Predict Waiting Time",
                description="Can we predict how long until the next eruption?",
                variables={"outcome": "waiting", "predictor": "eruptions"},
                query_example="Predict waiting time from eruption duration"
            ),
        ],
        tags=["bimodal", "geology", "prediction", "simple"],
        difficulty="beginner",
        learning_objectives=[
            "Practice simple linear regression",
            "Understand bimodal distributions",
            "Learn correlation and prediction",
        ]
    ),
}


class DatasetRegistry:
    """Registry for accessing built-in dataset information"""

    def __init__(self):
        self.datasets = BUILTIN_DATASETS

    def list_datasets(self, tags: Optional[List[str]] = None,
                     difficulty: Optional[str] = None) -> List[Dict]:
        """
        List available datasets with optional filtering.

        Args:
            tags: Filter by tags (e.g., ["biology", "regression"])
            difficulty: Filter by difficulty level

        Returns:
            List of dataset summaries
        """
        results = []

        for dataset_id, info in self.datasets.items():
            # Apply filters
            if tags:
                if not any(tag in info.tags for tag in tags):
                    continue

            if difficulty and info.difficulty != difficulty:
                continue

            results.append({
                "id": info.id,
                "name": info.name,
                "description": info.description[:150] + "..." if len(info.description) > 150 else info.description,
                "n_rows": info.n_rows,
                "n_cols": info.n_cols,
                "difficulty": info.difficulty,
                "tags": info.tags,
            })

        return results

    def get_dataset_info(self, dataset_id: str) -> Optional[DatasetInfo]:
        """Get full information about a specific dataset"""
        return self.datasets.get(dataset_id)

    def get_dataset_details(self, dataset_id: str) -> Optional[Dict]:
        """Get dataset details as a dictionary for JSON serialization"""
        info = self.get_dataset_info(dataset_id)
        if not info:
            return None

        return {
            "id": info.id,
            "name": info.name,
            "description": info.description,
            "source": info.source,
            "n_rows": info.n_rows,
            "n_cols": info.n_cols,
            "difficulty": info.difficulty,
            "tags": info.tags,
            "learning_objectives": info.learning_objectives,
            "variables": [
                {
                    "name": v.name,
                    "type": v.type.value,
                    "description": v.description,
                    "units": v.units,
                    "levels": v.levels,
                }
                for v in info.variables
            ],
            "suggested_analyses": [
                {
                    "type": a.type.value,
                    "title": a.title,
                    "description": a.description,
                    "variables": a.variables,
                    "query_example": a.query_example,
                }
                for a in info.suggested_analyses
            ],
        }

    def search_datasets(self, query: str) -> List[Dict]:
        """Search datasets by name, description, or tags"""
        query_lower = query.lower()
        results = []

        for dataset_id, info in self.datasets.items():
            score = 0

            # Check name
            if query_lower in info.name.lower():
                score += 3

            # Check description
            if query_lower in info.description.lower():
                score += 2

            # Check tags
            for tag in info.tags:
                if query_lower in tag.lower():
                    score += 1

            # Check variable names
            for var in info.variables:
                if query_lower in var.name.lower():
                    score += 1

            if score > 0:
                results.append({
                    "id": info.id,
                    "name": info.name,
                    "description": info.description[:100] + "...",
                    "score": score,
                    "difficulty": info.difficulty,
                })

        # Sort by relevance score
        results.sort(key=lambda x: x["score"], reverse=True)
        return results


# Singleton instance
_registry = None


def get_dataset_registry() -> DatasetRegistry:
    """Get or create the dataset registry singleton"""
    global _registry
    if _registry is None:
        _registry = DatasetRegistry()
    return _registry
