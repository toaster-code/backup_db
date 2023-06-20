import comtypes.client as client

# Create a new Word instance
word = client.CreateObject("Word.Application")

# Show the Word window (optional)
word.Visible = True

# Create a new document
doc = word.Documents.Add()

# Find style values dynamically
styles = doc.Styles
title1_style = styles("Title 1").StyleBasedOn
title2_style = styles("Title 2").StyleBasedOn
table_style = styles("Table Grid").StyleBasedOn

# Add a Title 1 heading
title1_text = "Title 1"
title1 = doc.Paragraphs.Add()
title1.Range.Text = title1_text
title1.Range.Style = title1_style

# Add a Title 2 heading
title2_text = "Title 2"
title2 = doc.Paragraphs.Add()
title2.Range.Text = title2_text
title2.Range.Style = title2_style

# Add a table
table = doc.Tables.Add(doc.Range(), 4, 3)  # 4 rows, 3 columns
table.Range.Style = table_style

# Populate the table with data
table.Cell(1, 1).Range.Text = "Header 1"
table.Cell(1, 2).Range.Text = "Header 2"
table.Cell(1, 3).Range.Text = "Header 3"

# Save the document
doc.SaveAs("styled_document.docx")  # Replace with your desired output file path

# Close the document and Word instance
doc.Close()
word.Quit()
