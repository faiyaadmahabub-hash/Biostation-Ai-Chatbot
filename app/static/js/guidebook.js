/**
 * ================================================
 * AI Capability Guidebook - JavaScript Module
 * A non-invasive, self-contained instructional panel
 * ================================================
 */

(function () {
    'use strict';

    // ============ GUIDEBOOK CONTENT DATA ============
    // All capabilities organized into user-friendly categories
    const GUIDEBOOK_DATA = {
        categories: [
            // ============ STATISTICAL TESTS REFERENCE (Educational) ============
            {
                id: 'statistical-tests',
                icon: 'auto_stories', // library_books or auto_stories
                title: 'Statistical Tests',
                description: 'Complete reference guide for all statistical tests',
                isReference: true,
                subcategories: [
                    {
                        name: 'Descriptive Statistics',
                        icon: 'bar_chart',
                        tests: [
                            {
                                id: 'ref-summary-stats',
                                title: 'Summary Statistics',
                                purpose: 'Summarizes your data with key numbers like averages, spread, and range. Answers: "What does my data look like overall?"',
                                whenToUse: 'As the first step in any analysis. Use with any numeric data to understand its central tendency and variability.',
                                whatYouNeed: 'One or more numeric columns from your dataset.',
                                prompt: 'Calculate summary statistics (mean, median, standard deviation, min, max) for my data'
                            },
                            {
                                id: 'ref-frequency',
                                title: 'Frequency Distribution',
                                purpose: 'Counts how often each value or category appears. Answers: "How are my values distributed?"',
                                whenToUse: 'When you want to see the distribution of categorical data or binned numeric data.',
                                whatYouNeed: 'A categorical column or numeric column you want to bin.',
                                prompt: 'Show me the frequency distribution of my categorical variable'
                            }
                        ]
                    },
                    {
                        name: 'Parametric Comparison Tests',
                        icon: 'balance',
                        description: 'For normally distributed data',
                        tests: [
                            {
                                id: 'ref-one-sample-t',
                                title: 'One-Sample T-Test',
                                purpose: 'Compares your sample average to a specific known value. Answers: "Is my sample mean different from this expected value?"',
                                whenToUse: 'When you have one group and want to compare it to a standard, target, or published value. Requires normally distributed data.',
                                whatYouNeed: 'A numeric column and a comparison value (the expected mean).',
                                prompt: 'Run a one-sample t-test to check if my sample mean differs from 100'
                            },
                            {
                                id: 'ref-independent-t',
                                title: 'Independent T-Test (Unpaired)',
                                purpose: 'Compares averages between two separate groups. Answers: "Is there a difference between Group A and Group B?"',
                                whenToUse: 'When comparing two independent groups (e.g., treatment vs control, male vs female). Requires normally distributed data in both groups.',
                                whatYouNeed: 'A numeric outcome column and a grouping column with exactly 2 groups.',
                                prompt: 'Compare the means between my treatment and control groups using an independent t-test'
                            },
                            {
                                id: 'ref-paired-t',
                                title: 'Paired T-Test',
                                purpose: 'Compares two measurements from the same subjects. Answers: "Did the values change significantly between time 1 and time 2?"',
                                whenToUse: 'When you measure the same subjects twice (before/after, pre/post). Requires the differences to be normally distributed.',
                                whatYouNeed: 'Two numeric columns representing paired measurements (before and after).',
                                prompt: 'Run a paired t-test comparing my before and after measurements'
                            },
                            {
                                id: 'ref-one-way-anova',
                                title: 'One-Way ANOVA',
                                purpose: 'Compares averages across 3 or more groups. Answers: "Is at least one group different from the others?"',
                                whenToUse: 'When comparing 3+ independent groups on one outcome variable. Requires normality and equal variances.',
                                whatYouNeed: 'A numeric outcome column and a grouping column with 3+ categories.',
                                prompt: 'Run ANOVA to compare my three treatment groups and show post-hoc results'
                            },
                            {
                                id: 'ref-two-way-anova',
                                title: 'Two-Way ANOVA',
                                purpose: 'Tests effects of two factors and their interaction. Answers: "Do both factors affect the outcome, and do they interact?"',
                                whenToUse: 'When you have two grouping variables (e.g., drug type AND dosage) and want to see their individual and combined effects.',
                                whatYouNeed: 'A numeric outcome and two categorical grouping columns.',
                                prompt: 'Run a two-way ANOVA with treatment and gender as factors'
                            },
                            {
                                id: 'ref-repeated-anova',
                                title: 'Repeated Measures ANOVA',
                                purpose: 'Compares the same subjects across 3+ conditions or time points. Answers: "Do measurements change across multiple time points?"',
                                whenToUse: 'When the same subjects are measured more than twice (e.g., at Week 1, Week 2, Week 4).',
                                whatYouNeed: 'Multiple numeric columns representing repeated measurements on the same subjects.',
                                prompt: 'Compare measurements across my three time points using repeated measures ANOVA'
                            }
                        ]
                    },
                    {
                        name: 'Non-Parametric Comparison Tests',
                        icon: 'sync_alt', // or swap_horiz
                        description: 'For non-normal or ordinal data',
                        tests: [
                            {
                                id: 'ref-mann-whitney',
                                title: 'Mann-Whitney U Test',
                                purpose: 'Compares two independent groups without assuming normal distribution. Answers: "Do the two groups differ in their distributions?"',
                                whenToUse: 'When comparing two independent groups but data is skewed, has outliers, or is ordinal (ranked).',
                                whatYouNeed: 'A numeric/ordinal outcome column and a grouping column with 2 groups.',
                                prompt: 'Compare my two groups using the Mann-Whitney U test (my data is not normally distributed)'
                            },
                            {
                                id: 'ref-wilcoxon',
                                title: 'Wilcoxon Signed-Rank Test',
                                purpose: 'Compares paired measurements without assuming normality. Answers: "Did paired values change significantly?"',
                                whenToUse: 'When you have paired/matched data that is not normally distributed.',
                                whatYouNeed: 'Two numeric columns representing paired measurements.',
                                prompt: 'Run Wilcoxon signed-rank test on my before and after data'
                            },
                            {
                                id: 'ref-kruskal',
                                title: 'Kruskal-Wallis Test',
                                purpose: 'Compares 3+ independent groups without assuming normality. Answers: "Is at least one group different?"',
                                whenToUse: 'When comparing 3+ groups with skewed, ordinal, or non-normal data.',
                                whatYouNeed: 'A numeric/ordinal outcome and a grouping column with 3+ categories.',
                                prompt: 'Compare my three groups using Kruskal-Wallis test (non-parametric)'
                            },
                            {
                                id: 'ref-friedman',
                                title: 'Friedman Test',
                                purpose: 'Non-parametric alternative to repeated measures ANOVA. Answers: "Do repeated measurements differ across conditions?"',
                                whenToUse: 'When the same subjects are measured 3+ times but data is not normally distributed.',
                                whatYouNeed: 'Multiple numeric columns representing repeated measurements.',
                                prompt: 'Run Friedman test to compare my repeated measurements across conditions'
                            }
                        ]
                    },
                    {
                        name: 'Correlation Tests',
                        icon: 'show_chart', // linear relationship
                        description: 'Measuring relationships between variables',
                        tests: [
                            {
                                id: 'ref-pearson',
                                title: 'Pearson Correlation',
                                purpose: 'Measures the strength of a linear relationship between two continuous variables. Answers: "How strongly are X and Y related in a straight line?"',
                                whenToUse: 'When both variables are continuous and normally distributed, and you expect a linear relationship.',
                                whatYouNeed: 'Two numeric columns.',
                                prompt: 'Calculate Pearson correlation between height and weight in my data'
                            },
                            {
                                id: 'ref-spearman',
                                title: 'Spearman Correlation',
                                purpose: 'Measures monotonic relationships (consistently increasing or decreasing). Answers: "Do X and Y move together consistently?"',
                                whenToUse: 'When data is ordinal, skewed, or the relationship is monotonic but not linear.',
                                whatYouNeed: 'Two numeric or ordinal columns.',
                                prompt: 'Calculate Spearman correlation between my variables (data is not normal)'
                            },
                            {
                                id: 'ref-kendall',
                                title: 'Kendall Tau Correlation',
                                purpose: 'A robust measure of ordinal association. Answers: "How strongly do rankings agree between two variables?"',
                                whenToUse: 'When you have ordinal data or small sample sizes. More robust than Spearman for ties.',
                                whatYouNeed: 'Two ordinal or ranked columns.',
                                prompt: 'Calculate Kendall tau correlation for my ranked data'
                            }
                        ]
                    },
                    {
                        name: 'Regression Tests',
                        icon: 'trending_up',
                        description: 'Predicting outcomes from predictors',
                        tests: [
                            {
                                id: 'ref-simple-linear',
                                title: 'Simple Linear Regression',
                                purpose: 'Predicts an outcome from a single predictor. Answers: "How does Y change when X changes?"',
                                whenToUse: 'When predicting a continuous outcome from one continuous predictor.',
                                whatYouNeed: 'One outcome (Y) column and one predictor (X) column, both numeric.',
                                prompt: 'Run simple linear regression predicting weight from height'
                            },
                            {
                                id: 'ref-multiple-linear',
                                title: 'Multiple Linear Regression',
                                purpose: 'Predicts an outcome from multiple predictors. Answers: "What factors influence Y, and by how much?"',
                                whenToUse: 'When predicting a continuous outcome from multiple predictors, controlling for confounders.',
                                whatYouNeed: 'One outcome column and two or more predictor columns.',
                                prompt: 'Run multiple regression predicting blood pressure from age, weight, and smoking status'
                            },
                            {
                                id: 'ref-logistic',
                                title: 'Logistic Regression',
                                purpose: 'Predicts a binary outcome (yes/no, success/failure). Answers: "What factors predict whether an event occurs?"',
                                whenToUse: 'When your outcome is binary (0/1, yes/no, alive/dead).',
                                whatYouNeed: 'A binary outcome column and one or more predictor columns.',
                                prompt: 'Run logistic regression predicting survival from age and treatment type'
                            },
                            {
                                id: 'ref-poisson',
                                title: 'Poisson Regression',
                                purpose: 'Models count data (number of events). Answers: "What factors affect the count of events?"',
                                whenToUse: 'When your outcome is a count (e.g., number of infections, number of offspring).',
                                whatYouNeed: 'A count outcome column and predictor columns.',
                                prompt: 'Run Poisson regression to predict the number of incidents based on my predictors'
                            }
                        ]
                    },
                    {
                        name: 'Categorical Data Tests',
                        icon: 'grid_view', // Table/grid metaphor
                        description: 'Analyzing categories and proportions',
                        tests: [
                            {
                                id: 'ref-chi-squared',
                                title: 'Chi-Squared Test',
                                purpose: 'Tests if two categorical variables are associated. Answers: "Is there a relationship between category A and category B?"',
                                whenToUse: 'When both variables are categorical and expected cell counts are ≥ 5.',
                                whatYouNeed: 'Two categorical columns.',
                                prompt: 'Run a chi-squared test to see if treatment response is associated with gender'
                            },
                            {
                                id: 'ref-fisher',
                                title: "Fisher's Exact Test",
                                purpose: 'Tests categorical association with small samples. Answers: "Are categories associated when sample is small?"',
                                whenToUse: 'When sample is small or any expected cell count is less than 5.',
                                whatYouNeed: 'Two categorical columns (typically a 2x2 table).',
                                prompt: "Run Fisher's exact test on my 2x2 contingency table"
                            },
                            {
                                id: 'ref-mcnemar',
                                title: "McNemar's Test",
                                purpose: 'Compares paired proportions. Answers: "Did the proportion of yes/no responses change between two time points?"',
                                whenToUse: 'When you have paired binary outcomes (same subjects before/after).',
                                whatYouNeed: 'Two binary columns representing paired categorical outcomes.',
                                prompt: "Run McNemar's test to compare the proportion of positive responses before and after treatment"
                            }
                        ]
                    },
                    {
                        name: 'Assumption Tests',
                        icon: 'rule', // or check_circle_outline
                        description: 'Checking if your data meets test requirements',
                        tests: [
                            {
                                id: 'ref-shapiro',
                                title: 'Shapiro-Wilk Normality Test',
                                purpose: 'Tests if data is normally distributed. Answers: "Can I use parametric tests on this data?"',
                                whenToUse: 'Before running t-tests or ANOVA to verify the normality assumption.',
                                whatYouNeed: 'A numeric column (works best with n < 5000).',
                                prompt: 'Check if my data is normally distributed using Shapiro-Wilk test'
                            },
                            {
                                id: 'ref-levene',
                                title: "Levene's Test",
                                purpose: 'Tests if variances are equal across groups. Answers: "Do my groups have similar spread?"',
                                whenToUse: 'Before ANOVA or t-tests to check the equal variance (homoscedasticity) assumption.',
                                whatYouNeed: 'A numeric outcome column and a grouping column.',
                                prompt: "Run Levene's test to check if variances are equal between my groups"
                            },
                            {
                                id: 'ref-qq-plot',
                                title: 'Q-Q Plot',
                                purpose: 'Visually shows if data follows a normal distribution. Answers: "Does my data look normal?"',
                                whenToUse: 'As a visual complement to normality tests. Points should fall on the diagonal line if normal.',
                                whatYouNeed: 'A numeric column.',
                                prompt: 'Create a Q-Q plot to visually check normality of my data'
                            }
                        ]
                    }
                ],
                items: [] // This category uses subcategories instead of items
            },
            {
                id: 'test-selection',
                icon: 'explore',
                title: 'Choosing the Right Test',
                description: 'Get guided help selecting a test',
                items: [
                    {
                        id: 'advisor',
                        title: 'Statistical Test Advisor',
                        badge: 'recommended',
                        whatItDoes: 'An interactive guide that asks you questions about your data and research question, then recommends the most appropriate statistical test.',
                        whenToUse: 'When you are unsure which statistical test to use for your analysis.',
                        steps: [
                            'Ask for help choosing a test',
                            'Answer the questions about your research',
                            'The AI will guide you through the decision tree'
                        ],
                        prompts: [
                            'Which statistical test should I use?',
                            'Help me choose the right test for my data',
                            'I want to compare groups - what test is appropriate?',
                            'Guide me through selecting a statistical test'
                        ]
                    }
                ]
            },
            {
                id: 'code',
                icon: 'code',
                title: 'R Code Generation',
                description: 'Get ready-to-run R code',
                items: [
                    {
                        id: 'generate-code',
                        title: 'Generate R Code',
                        badge: null,
                        whatItDoes: 'Creates complete, runnable R code for any statistical analysis. Includes data loading, tests, diagnostic checks, and visualizations.',
                        whenToUse: 'When you want R code that you can run in RStudio or any R environment.',
                        steps: [
                            'Describe the analysis you want',
                            'Upload your data or specify the data format',
                            'The AI generates complete R code with comments',
                            'Use the "Open in Editor" button to edit and run'
                        ],
                        prompts: [
                            'Generate R code for a t-test comparing my groups',
                            'Write R code to run ANOVA on my data',
                            'Give me the R code for Pearson correlation with visualization'
                        ]
                    },
                    {
                        id: 'run-code',
                        title: 'Run R Code',
                        badge: null,
                        whatItDoes: 'Execute R code directly in BioStation. View outputs, plots, and results without leaving the application.',
                        whenToUse: 'When you want to run and test R code immediately.',
                        steps: [
                            'Click "Open in Editor" on any code block',
                            'Edit the code if needed',
                            'Click "Run" to execute',
                            'View results in the output panel'
                        ],
                        prompts: [
                            'Run this R code for me',
                            'Execute the analysis and show me the output',
                            'Open the code editor so I can run my script'
                        ]
                    }
                ]
            },
            {
                id: 'help',
                icon: 'build',
                title: 'Learning & Debugging',
                description: 'Understand concepts and fix errors',
                items: [
                    {
                        id: 'explain',
                        title: 'Explain Concepts',
                        badge: null,
                        whatItDoes: 'Provides clear, beginner-friendly explanations of statistical concepts, tests, and terminology.',
                        whenToUse: 'When you want to understand what a test does, when to use it, or what results mean.',
                        steps: [
                            'Ask about any statistical concept',
                            'The AI explains in simple, non-technical terms',
                            'Ask follow-up questions for clarification'
                        ],
                        prompts: [
                            'What is a p-value and what does it mean?',
                            'Explain the difference between parametric and non-parametric tests',
                            'What does the confidence interval tell me?',
                            'When should I use ANOVA vs t-test?'
                        ]
                    },
                    {
                        id: 'debug',
                        title: 'Debug R Errors',
                        badge: null,
                        whatItDoes: 'Helps you understand and fix errors in your R code. Explains error messages and suggests solutions.',
                        whenToUse: 'When you encounter an error message and do not know how to fix it.',
                        steps: [
                            'Paste the error message',
                            'Include the code that caused it (if possible)',
                            'The AI will explain the problem and suggest fixes'
                        ],
                        prompts: [
                            'I got this error: [paste error] - what does it mean?',
                            'Why is my R code not working?',
                            'Help me debug this error message',
                            'Fix this code: [paste code]'
                        ]
                    },
                    {
                        id: 'interpret',
                        title: 'Interpret Results',
                        badge: null,
                        whatItDoes: 'Helps you understand what your statistical results mean in plain language.',
                        whenToUse: 'After running an analysis when you need help understanding the output.',
                        steps: [
                            'Share your statistical output',
                            'Ask for an interpretation',
                            'Get a plain-language summary'
                        ],
                        prompts: [
                            'What do these results mean?',
                            'Is this p-value significant?',
                            'Interpret my ANOVA output',
                            'Explain this regression output in simple terms'
                        ]
                    }
                ]
            }
        ]
    };

    // ============ STATE ============
    let isOpen = false;
    let expandedCategories = new Set();
    let expandedItems = new Set();

    // ============ INITIALIZATION ============
    function init() {
        createPanelHTML();
        attachEventListeners();
        renderContent();
        console.log('AI Capability Guidebook initialized');
    }

    // ============ CREATE PANEL HTML ============
    function createPanelHTML() {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'guidebook-overlay';
        overlay.id = 'guidebook-overlay';
        document.body.appendChild(overlay);

        // Create panel
        const panel = document.createElement('div');
        panel.className = 'guidebook-panel';
        panel.id = 'guidebook-panel';
        panel.innerHTML = `
            <div class="guidebook-drag-handle" id="guidebook-drag-handle" title="Drag to resize"></div>
            <div class="guidebook-header">
                <h2 class="guidebook-title">
                    <span class="material-icons-round guidebook-title-icon">menu_book</span>
                    AI Capability Guide
                </h2>
                <button class="guidebook-close-btn" id="guidebook-close-btn" title="Close">
                    <span class="material-icons-round">close</span>
                </button>
            </div>
            <div class="guidebook-search">
                <div class="guidebook-search-wrapper">
                    <span class="material-icons-round guidebook-search-icon">search</span>
                    <input type="text" 
                           class="guidebook-search-input" 
                           id="guidebook-search-input"
                           placeholder="Search capabilities...">
                </div>
            </div>
            <div class="guidebook-content" id="guidebook-content">
                <!-- Content rendered by JavaScript -->
            </div>
            <div class="guidebook-footer">
                Click any example prompt, then paste it in the chat to get started.
            </div>
        `;
        document.body.appendChild(panel);

        // Add toggle button to top bar
        const topBar = document.querySelector('.top-bar');
        if (topBar) {
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'guidebook-toggle-btn';
            toggleBtn.id = 'guidebook-toggle-btn';
            toggleBtn.title = 'AI Capability Guide';
            toggleBtn.innerHTML = '<span class="material-icons-round">menu_book</span>';
            topBar.appendChild(toggleBtn);
        }
    }

    // ============ RENDER CONTENT ============
    function renderContent(filterText = '') {
        const container = document.getElementById('guidebook-content');
        if (!container) return;

        const filter = filterText.toLowerCase().trim();
        let hasResults = false;

        let html = '';

        GUIDEBOOK_DATA.categories.forEach(category => {
            // Handle reference categories with subcategories
            if (category.isReference && category.subcategories) {
                const filteredSubcategories = category.subcategories.map(sub => {
                    const filteredTests = sub.tests.filter(test => {
                        if (!filter) return true;
                        return test.title.toLowerCase().includes(filter) ||
                            test.purpose.toLowerCase().includes(filter) ||
                            test.prompt.toLowerCase().includes(filter);
                    });
                    return { ...sub, tests: filteredTests };
                }).filter(sub => sub.tests.length > 0);

                if (filteredSubcategories.length === 0) return;
                hasResults = true;

                const isCategoryExpanded = expandedCategories.has(category.id) || filter;

                html += `
                    <div class="guidebook-category guidebook-reference ${isCategoryExpanded ? 'expanded' : ''}" data-category-id="${category.id}">
                        <div class="guidebook-category-header">
                            <div class="guidebook-category-icon"><span class="material-icons-round">${category.icon}</span></div>
                            <span class="guidebook-category-title">${category.title}</span>
                            <span class="guidebook-badge new">Reference</span>
                            <span class="material-icons-round guidebook-category-chevron">expand_more</span>
                        </div>
                        <div class="guidebook-category-items">
                            ${renderSubcategories(filteredSubcategories, filter)}
                        </div>
                    </div>
                `;
                return;
            }

            // Standard categories with items
            const filteredItems = category.items.filter(item => {
                if (!filter) return true;
                return item.title.toLowerCase().includes(filter) ||
                    item.whatItDoes.toLowerCase().includes(filter) ||
                    item.prompts.some(p => p.toLowerCase().includes(filter));
            });

            if (filteredItems.length === 0) return;
            hasResults = true;

            const isCategoryExpanded = expandedCategories.has(category.id) || filter;

            html += `
                <div class="guidebook-category ${isCategoryExpanded ? 'expanded' : ''}" data-category-id="${category.id}">
                    <div class="guidebook-category-header">
                        <div class="guidebook-category-icon"><span class="material-icons-round">${category.icon}</span></div>
                        <span class="guidebook-category-title">${category.title}</span>
                        <span class="material-icons-round guidebook-category-chevron">expand_more</span>
                    </div>
                    <div class="guidebook-category-items">
                        ${renderItems(filteredItems, filter)}
                    </div>
                </div>
            `;
        });

        if (!hasResults) {
            html = `
                <div class="guidebook-no-results">
                    <div class="guidebook-no-results-icon">🔍</div>
                    <div class="guidebook-no-results-text">No capabilities match your search.</div>
                </div>
            `;
        }

        container.innerHTML = html;
        attachItemListeners();
    }

    // ============ RENDER SUBCATEGORIES (for Statistical Tests Reference) ============
    function renderSubcategories(subcategories, filter) {
        return subcategories.map(sub => {
            const isSubExpanded = expandedCategories.has(`sub-${sub.name}`) || filter;

            return `
                <div class="guidebook-subcategory ${isSubExpanded ? 'expanded' : ''}" data-subcategory-name="${sub.name}">
                    <div class="guidebook-subcategory-header">
                        <span class="guidebook-subcategory-icon"><span class="material-icons-round">${sub.icon}</span></span>
                        <span class="guidebook-subcategory-title">${sub.name}</span>
                        ${sub.description ? `<span class="guidebook-subcategory-desc">${sub.description}</span>` : ''}
                        <span class="material-icons-round guidebook-subcategory-chevron">expand_more</span>
                    </div>
                    <div class="guidebook-subcategory-tests">
                        ${renderReferenceTests(sub.tests, filter)}
                    </div>
                </div>
            `;
        }).join('');
    }

    // ============ RENDER REFERENCE TESTS ============
    function renderReferenceTests(tests, filter) {
        return tests.map(test => {
            const isExpanded = expandedItems.has(test.id) || (filter && tests.length === 1);

            return `
                <div class="guidebook-ref-test ${isExpanded ? 'expanded' : ''}" data-item-id="${test.id}">
                    <div class="guidebook-ref-test-header">
                        <span class="guidebook-ref-test-title">${test.title}</span>
                        <span class="material-icons-round guidebook-item-chevron">expand_more</span>
                    </div>
                    <div class="guidebook-ref-test-details">
                        <div class="guidebook-ref-test-content">
                            <div class="guidebook-ref-section">
                                <div class="guidebook-ref-label">
                                    <span class="material-icons-round">help_outline</span> Purpose
                                </div>
                                <div class="guidebook-ref-text">${test.purpose}</div>
                            </div>
                            
                            <div class="guidebook-ref-section">
                                <div class="guidebook-ref-label">
                                    <span class="material-icons-round">schedule</span> When to Use
                                </div>
                                <div class="guidebook-ref-text">${test.whenToUse}</div>
                            </div>
                            
                            <div class="guidebook-ref-section">
                                <div class="guidebook-ref-label">
                                    <span class="material-icons-round">checklist</span> What You Need
                                </div>
                                <div class="guidebook-ref-text">${test.whatYouNeed}</div>
                            </div>
                            
                            <div class="guidebook-ref-section">
                                <div class="guidebook-ref-label">
                                    <span class="material-icons-round">chat</span> Example Prompt
                                </div>
                                <div class="guidebook-prompt" data-prompt="${escapeAttr(test.prompt)}">
                                    <div class="guidebook-prompt-text">${test.prompt}</div>
                                    <button class="guidebook-prompt-copy">
                                        <span class="material-icons-round">content_copy</span>
                                        Copy
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function renderItems(items, filter) {
        return items.map(item => {
            const isExpanded = expandedItems.has(item.id) || (filter && items.length === 1);
            const badgeHTML = item.badge ? `<span class="guidebook-badge ${item.badge}">${item.badge}</span>` : '';

            return `
                <div class="guidebook-item ${isExpanded ? 'expanded' : ''}" data-item-id="${item.id}">
                    <div class="guidebook-item-header">
                        <span class="guidebook-item-title">${item.title}${badgeHTML}</span>
                        <span class="material-icons-round guidebook-item-chevron">expand_more</span>
                    </div>
                    <div class="guidebook-item-details">
                        <div class="guidebook-item-content">
                            <div class="guidebook-section">
                                <div class="guidebook-section-label">
                                    <span class="material-icons-round">info</span> What It Does
                                </div>
                                <div class="guidebook-section-text">${item.whatItDoes}</div>
                            </div>
                            
                            <div class="guidebook-section">
                                <div class="guidebook-section-label">
                                    <span class="material-icons-round">schedule</span> When To Use
                                </div>
                                <div class="guidebook-section-text">${item.whenToUse}</div>
                            </div>
                            
                            <div class="guidebook-section">
                                <div class="guidebook-section-label">
                                    <span class="material-icons-round">format_list_numbered</span> How To Ask
                                </div>
                                <ol class="guidebook-steps">
                                    ${item.steps.map(step => `<li class="guidebook-step">${step}</li>`).join('')}
                                </ol>
                            </div>
                            
                            <div class="guidebook-section">
                                <div class="guidebook-section-label">
                                    <span class="material-icons-round">chat</span> Example Prompts
                                </div>
                                ${item.prompts.map(prompt => `
                                    <div class="guidebook-prompt" data-prompt="${escapeAttr(prompt)}">
                                        <div class="guidebook-prompt-text">${prompt}</div>
                                        <button class="guidebook-prompt-copy">
                                            <span class="material-icons-round">content_copy</span>
                                            Copy
                                        </button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    function escapeAttr(str) {
        return str.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    // ============ EVENT LISTENERS ============
    function attachEventListeners() {
        // Toggle button
        const toggleBtn = document.getElementById('guidebook-toggle-btn');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', togglePanel);
        }

        // Close button
        const closeBtn = document.getElementById('guidebook-close-btn');
        if (closeBtn) {
            closeBtn.addEventListener('click', closePanel);
        }

        // Overlay click
        const overlay = document.getElementById('guidebook-overlay');
        if (overlay) {
            overlay.addEventListener('click', closePanel);
        }

        // Search input
        const searchInput = document.getElementById('guidebook-search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                renderContent(e.target.value);
            });
        }

        // Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && isOpen) {
                closePanel();
            }
        });


        // Initialize Resize Handler
        initResizeHandler();
    }

    // ============ RESIZE HANDLER ============
    function initResizeHandler() {
        const panel = document.getElementById('guidebook-panel');
        const handle = document.getElementById('guidebook-drag-handle');

        if (!panel || !handle) return;

        let startX, startWidth;

        const onMouseDown = (e) => {
            startX = e.clientX;
            startWidth = parseInt(document.defaultView.getComputedStyle(panel).width, 10);

            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);

            panel.classList.add('resizing');
            handle.classList.add('dragging');

            // Prevent text selection
            document.body.style.userSelect = 'none';
        };

        const onMouseMove = (e) => {
            // Panel is on the right, so dragging left (smaller X) increases width
            // newWidth = startWidth + (startX - currentX)
            const newWidth = startWidth + (startX - e.clientX);

            // Constraints
            const maxWidth = window.innerWidth * 0.9;
            const minWidth = 300;

            if (newWidth >= minWidth && newWidth <= maxWidth) {
                panel.style.width = `${newWidth}px`;
            }
        };

        const onMouseUp = () => {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);

            panel.classList.remove('resizing');
            handle.classList.remove('dragging');
            document.body.style.userSelect = '';
        };

        handle.addEventListener('mousedown', onMouseDown);
    }

    function attachItemListeners() {
        // Category headers
        document.querySelectorAll('.guidebook-category-header').forEach(header => {
            header.addEventListener('click', () => {
                const category = header.closest('.guidebook-category');
                const categoryId = category.dataset.categoryId;

                if (expandedCategories.has(categoryId)) {
                    expandedCategories.delete(categoryId);
                    category.classList.remove('expanded');
                } else {
                    expandedCategories.add(categoryId);
                    category.classList.add('expanded');
                }
            });
        });

        // Subcategory headers (for Statistical Tests Reference)
        document.querySelectorAll('.guidebook-subcategory-header').forEach(header => {
            header.addEventListener('click', (e) => {
                e.stopPropagation();
                const subcategory = header.closest('.guidebook-subcategory');
                const subName = subcategory.dataset.subcategoryName;
                const key = `sub-${subName}`;

                if (expandedCategories.has(key)) {
                    expandedCategories.delete(key);
                    subcategory.classList.remove('expanded');
                } else {
                    expandedCategories.add(key);
                    subcategory.classList.add('expanded');
                }
            });
        });

        // Reference test headers
        document.querySelectorAll('.guidebook-ref-test-header').forEach(header => {
            header.addEventListener('click', (e) => {
                e.stopPropagation();
                const test = header.closest('.guidebook-ref-test');
                const testId = test.dataset.itemId;

                if (expandedItems.has(testId)) {
                    expandedItems.delete(testId);
                    test.classList.remove('expanded');
                } else {
                    expandedItems.add(testId);
                    test.classList.add('expanded');
                }
            });
        });

        // Item headers (standard items)
        document.querySelectorAll('.guidebook-item-header').forEach(header => {
            header.addEventListener('click', (e) => {
                e.stopPropagation();
                const item = header.closest('.guidebook-item');
                const itemId = item.dataset.itemId;

                if (expandedItems.has(itemId)) {
                    expandedItems.delete(itemId);
                    item.classList.remove('expanded');
                } else {
                    expandedItems.add(itemId);
                    item.classList.add('expanded');
                }
            });
        });

        // Copy buttons
        document.querySelectorAll('.guidebook-prompt-copy').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const promptDiv = btn.closest('.guidebook-prompt');
                const promptText = promptDiv.dataset.prompt;

                copyToClipboard(promptText, btn);
            });
        });

        // Clicking on prompt itself also copies
        document.querySelectorAll('.guidebook-prompt').forEach(promptDiv => {
            promptDiv.addEventListener('click', (e) => {
                e.stopPropagation();
                const promptText = promptDiv.dataset.prompt;
                const btn = promptDiv.querySelector('.guidebook-prompt-copy');
                copyToClipboard(promptText, btn);
            });
        });
    }

    // ============ COPY TO CLIPBOARD ============
    function copyToClipboard(text, btn) {
        navigator.clipboard.writeText(text).then(() => {
            // Visual feedback
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="material-icons-round">check</span> Copied!';
            btn.classList.add('copied');

            setTimeout(() => {
                btn.innerHTML = originalText;
                btn.classList.remove('copied');
            }, 1500);

            // Also paste into chat input if available
            const chatInput = document.getElementById('user-input');
            if (chatInput) {
                chatInput.value = text;
                chatInput.focus();
                // Trigger input event to enable send button
                chatInput.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    }

    // ============ PANEL TOGGLE ============
    function togglePanel() {
        if (isOpen) {
            closePanel();
        } else {
            openPanel();
        }
    }

    function openPanel() {
        const panel = document.getElementById('guidebook-panel');
        const overlay = document.getElementById('guidebook-overlay');
        const toggleBtn = document.getElementById('guidebook-toggle-btn');

        if (panel) panel.classList.add('open');
        if (overlay) overlay.classList.add('visible');
        if (toggleBtn) toggleBtn.classList.add('active');

        isOpen = true;
    }

    function closePanel() {
        const panel = document.getElementById('guidebook-panel');
        const overlay = document.getElementById('guidebook-overlay');
        const toggleBtn = document.getElementById('guidebook-toggle-btn');

        if (panel) panel.classList.remove('open');
        if (overlay) overlay.classList.remove('visible');
        if (toggleBtn) toggleBtn.classList.remove('active');

        isOpen = false;

        // Clear search
        const searchInput = document.getElementById('guidebook-search-input');
        if (searchInput) searchInput.value = '';
    }

    // ============ EXPOSE GLOBAL API (optional) ============
    window.BioStationGuidebook = {
        open: openPanel,
        close: closePanel,
        toggle: togglePanel
    };

    // ============ INITIALIZE ON DOM READY ============
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
