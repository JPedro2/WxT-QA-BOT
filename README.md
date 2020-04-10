# WxT-QA-BOT
This Webex Teams bot is being developed to help Cisco and IBM volunteers that will be supporting teachers and charities, across the UK, to access free video conferencing through the use of Cisco Webex Meetings

**Front-end Information**
- Front-end is a simple static .HTML site with a form pushing to our API route /addEntry
- Utilising StatiCrypt for simple page encryption (https://www.npmjs.com/package/staticrypt) 
- Current page is password protected using the password "webexisawesome"
- Page hosted at https://app.netlify.com/sites/suspicious-mayer-f99e85/overview using my netlify account
- Currently manually deploying the site due to having to run the staticrypt script after updating, but this could be automated with a pipeline

** GCP SQL Info **
- Public IP : 35.246.123.175
- Username: root | Password: lalol~
- Database Name : qanda | Database Table : qanda
