# Function to ensure packages are installed
ensure_package <- function(pkg) {{
  if (!require(pkg, character.only = TRUE)) {{
    cat(paste("Installing missing package:", pkg, "\n"))
    install.packages(pkg, repos = "https://cloud.r-project.org")
    if (!require(pkg, character.only = TRUE)) {{
      stop(paste("Failed to install package:", pkg))
    }}
  }}
}}
