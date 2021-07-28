library(shiny)
library(shinyLP)
library(DT)
library(readxl)

# Setup ----

# Create a list of samples based on the files present in the kraken output directory
isolates <- list.files(path = "www")

# Get only the sample names from the file list (everything before "_")
isolates <- sub("_.*", "", isolates)

# Get the unique samples names
isolates <- unique(isolates)

# Define UI for application ----
ui <- fluidPage(
    
    # Define page layout ----
    verticalLayout(
        
        # Render user options panel ----
        wellPanel(
            
            # User input to choose sample of interest to view ----
            selectizeInput("isolate",
                           h4("Select or search for an isolate:"),
                           choices = NULL,
                           options = list(maxItems = 1)),
        ),
        
        # Render plots/tables panel ----
        wellPanel(
            
            # Plot recentrifuge plot ----
            htmlOutput("recentrifuge_plot")
            
            # # Render recentrifuge table ----
            # dataTableOutput("recentrifuge_table")
            
        )
    )
)

# Define server logic required for the application ----
server <- function(input, output, session) {
    
    # Get the current isolate the user has chosen to view ----
    updateSelectizeInput(session, "isolate", choices = isolates, server=TRUE)
    
    # Build a path to the recentrifuge html file based on the current isolate the user has chosen to view ----
    observe({ 
        # Extract as context path variable  (environment variable?)
        recentrifuge_html_path <<- paste0("/POC_metagenomics_dashboard/", input$isolate, "_kr2_output.krk.rcf.html")
    })
    
    # Embed the appropriate recentrifuge html file in the dashboard ----
    output$recentrifuge_plot <- renderUI({
        
        # Print a message if no isolate is chosen
        validate(need(input$isolate, "Please choose and isolate from the drop down box to create a plot"))
        
        # Load in the current isolate the user has chosen to view so it can be used for "recentrifuge_html_path" ----
        input$isolate

        plot <- tags$iframe(src=recentrifuge_html_path, height=1000, width="100%")
        plot
    })
    
    # # Create interactive table of the appropriate recentrifuge xlsx file in the dashboard ----
    # output$recentrifuge_table <- renderDataTable({
    # 
    #     input$isolate
    #     
    #     datatable(read_excel(paste0("/POC_metagenomics_dashboard/", input$isolate, "_kr2_output.krk.rcf.xlsx")),
    #               filter = "top",
    #               rownames = FALSE,
    #               # colnames = c("RNA",
    #               #              "RNA species",
    #               #              "Pipeline",
    #               #              "Differential expression method",
    #               #              "Log fold change (limma voom)",
    #               #              "Log fold change (deseq2)",
    #               #              "Adjusted p-value (limma voom)",
    #               #              "Adjusted p-value (deseq2)",
    #               #              "Significance"),
    #               extensions = list("ColReorder" = NULL,
    #                                 "Buttons" = NULL,
    #                                 "FixedColumns" = list(leftColumns=1)),
    #               options = list(
    #                   dom = "BRrltpi",
    #                   autoWidth = TRUE,
    #                   columnDefs = list(list(width = "200px", targets = 0)),
    #                   lengthMenu = list(c(10, 50, -1), c("10", "50", "All")),
    #                   ColReorder = TRUE,
    #                   buttons =
    #                       list("copy",
    #                            list(extend = "collection",
    #                                 buttons = c("csv", "excel", "pdf"),
    #                                 text = "Download"),
    #                            I("colvis")))) 
    # })
}

# Run the application 
shinyApp(ui = ui, server = server)
