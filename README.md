# HubSpot job title cleaner for Operations Hub
 Cleans Job TItle fields with a Custom coded action (using Python) in HubSpot operations hub 

This is an early proof of concept test and should be tested first.

Results
On a test sandbox with 100,000 multi-lingual job title values in business and science / research sectors, the script:
- Removed 800 values entirely, made 1,200 major changes and 23,000 minor changes.
- removed illegal entries like email address, single characters, or where the value was just a special character e.g. * or ! or @
- removed illegal characters at the start and end of job .
- ignores data in non-latin character set (e.g. Japanese, Korean, Chinese).
- fixed many formatting issues with capitalisation
- removed entries with multiple repeating characters mixed with other data e.g. "aaaa" or "jooooob title".
- Preserved data that could be a science roll.
- preserved all valid data (whoop!)

What it did not clean or remove, or other issues:
- Remove values which are strings of jumbled characters (very difficult to figure out if the job title makes sense). e.g. jqocleruair (These were almost always spam where the contact record could be removed using other tests). This is very difficult to do in a multi-lingual way without referencing dictionaries for official words.
- did not remove properly formated text values which are junk e..g "No thank you"
- Changed 1st to 1St, 2nd to 2Nd. etc.

Future development / next steps
After cleaning the data, a call could be made to ChatGPT to ask it to validate any remaining value to see if it is a valid job title.
 
=========================
Overview
=========================

A testing script for a local pythnon environment is also included in job_title_cleaning.py.
The test script will load a list of job title data from a file you need to prepare called "job_titles.csv". The file should consist of a single column  of job title values.
It will clean it and output a new file. To make it easy to review this is an indexed list of original values side by side with the cleaned values. 

Anomylous and bad data is removed.
Extrenous data such as commas and spaces will be removed from the beginning of lines.
Poorly formmatted data is corrected (Capitalisation, double spaces)
Values that are phone numbers or just numbers will be removed.

 This code should be thoroughly tested before deployment as it could irreversibly delete or damage data.
 Use it in a sandbox environment first.
 No warranty is offered.

The code will take the Job Title, clean it and store it as a variable "newTitle" which needs to be used in a subsequent workflow action to write this back to the jobTitle.

=========================
Summary of cleaning actions:
=========================
Ignores non-latin strings (e.g Chinese, Japanese, Russian, Greek etc)
Removal of leading punctuation, spaces, quotes, or parentheses if the entire value is enclosed.
Diacritics conversion (e.g. “ä” → “a”) instead of discarding foreign text.
Filtering out numeric-only values, phone-like formats (7+ digits), and known “junk” entries (such as “n/a”, “no”, “test”, etc.).
Removal of email address.
Capitalisation rules:
Preserve certain acronyms in uppercase (e.g. “IT”, “AIO”, “APHL”).
Convert “phd” to “PhD”.
Ensure Roman numerals (I–IX) are uppercase when attached to a preceding word.
Other normalisations:
Convert vertical bars (|) to commas.
Only lowercase “And” when found between words.
Keep “Post Doc” from becoming fully uppercase.
Return empty if the final string is invalid.

=============
How to set up in HubSpot
=============
Step 1: Triggers
You can set this to run when a contact is created, or when the job title field is changed.
You could also set it to run periodically. You will need to set contact to re-enroll.

For testing leave this as manual enrollment and allow contacts to re-enroll.

Step 2: get the Job Title property value and clean it.
Add the custom coded workflow action in a hubspot workflow
Select Python as the scripting language
Set "jobTitle" as a input key and select the Job Title field for the contact record.
Get the contents of custom-code.py
For output keys:
"newTitle" as a string datatype.
"outcome" as a string datatype.

Step 3: write the cleaned value back to the job Title field
The script will set "outcome" as "no_change" if no change has been made to the job title, and "success" if it has been cleaned.
You can use this data to only write changes back to contact records where the data has been cleaned
Create a single branch but change the top drop-down from "enrolled contact" to "Action Outcomes" and then select "outcome".
Set the logic to "is equal to" and the value to "changed" and save it.
In the success branch add another action. The action type shoud be CRM - edit record.
Select the Job Title property and then select "newTitle" for the property.

Save and enable the workflow

Run tests and validate that the script is cleaning or ignoring unchanged contacts.

For more informatino check out the HubSpot KB on custom coded actions:
https://developers.hubspot.com/docs/reference/api/automation/custom-code-actions
