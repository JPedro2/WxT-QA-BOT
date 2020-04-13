# WxT-QA-BOT
This Webex Teams bot is being developed to help Cisco and IBM volunteers that will be supporting teachers and charities, across the UK, to access free video conferencing through the use of Cisco Webex Meetings

**Front-end Information**
- Front-end is a simple static .HTML site with a form pushing to our API route /addEntry
- Utilising StatiCrypt for simple page encryption (https://www.npmjs.com/package/staticrypt) 
- Page hosted at https://app.netlify.com/sites/suspicious-mayer-f99e85/overview using my netlify account
- Currently manually deploying the site due to having to run the staticrypt script after updating, but this could be automated with a pipeline

**Back-end Information**
- Flask
- Two functions currently implemented:
    - `getAnswer()` (`/getAnswer` or `/getAnswer/<question>`) returns the answer given a question, as well as the location of an associated resource
    - `addEntry()` (`/addEntry`) inserts a new row into `qanda` given a tag, question, answer, and (optionally) a location
- Default limit is 100 requests per day, 10 requests per hour (per IP address)
- `getAnswer()` is additionally limited to 1 request per minute
- `addEntry()` is exempt from limits

**GCP SQL Info**
- Database Name : qanda | Database Table : qanda

```sql
id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
tag VARCHAR(50) NOT NULL,
question VARCHAR(2000) NOT NULL,
answer VARCHAR(2000) NOT NULL,
location VARCHAR(255)
```
