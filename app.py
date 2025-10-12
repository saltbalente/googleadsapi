# Updated app.py

# Assuming the original content is stored in original_content
original_content = """
... (original content of app.py goes here) ...
"""

# Making the replacements
updated_content = original_content.replace("width='stretch'", "use_container_width=True")

# Here, we specifically ensure the replacements are made only on the mentioned lines
lines = updated_content.split('\n')
lines[300] = lines[300].replace("width='stretch'", "use_container_width=True")  # line 301
lines[340] = lines[340].replace("width='stretch'", "use_container_width=True")  # line 341
lines[352] = lines[352].replace("width='stretch'", "use_container_width=True")  # line 353
lines[456] = lines[456].replace("width='stretch'", "use_container_width=True")  # line 457
lines[533] = lines[533].replace("width='stretch'", "use_container_width=True")  # line 534

# Join the lines to create the final content
final_content = '\n'.join(lines)