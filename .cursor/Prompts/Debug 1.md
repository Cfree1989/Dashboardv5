You are an expert Incident Response Engineer tasked with incident diagnosis & resolution. Isolate the root cause of failures and record details, perform root cause analysis, and recommend preventative measures.

We must get to the bottom of this issue as soon as possible, through thorough Run a root cause analysis on:

Our Current Problem Reported: 

The Symptom: A Ghost in the Machine
From your perspective, the problem was straightforward but maddening:
You approve a job in the "UPLOADED" tab.
The modal closes, but the job is still there.
The tab count for "UPLOADED" remains unchanged.
After a seemingly random delay of 45-90 seconds, the job suddenly vanishes and the count updates.
A similar delay was happening for newly submitted jobs appearing.
This pointed to some kind of caching issue, but the question was, where?
The Investigation: Ruling Out the Obvious
We went through a systematic process of elimination:
Is it the Frontend? We added extensive logging to the frontend. This showed that the frontend was correctly asking the backend for fresh data (fetchJobs(true)). However, the backend's API was sending back the old list of jobs, even after the approval was successful. This proved the frontend was not the problem.
Is the Backend Commit Slow? We then suspected the backend was slow to save the change to the database. We added detailed timing logs to the approval process. This proved the database commit was incredibly fast—taking only a few milliseconds. The backend thought it had saved the data instantly.
Is it a Caching Layer? We checked for any explicit caching systems. We looked at the Nginx configuration and the Python requirements.txt. There was no evidence of a proxy cache or a library like Flask-Caching that would hold onto old API results.
The Breakthrough: The External Database Check
This is where the external_db_check.py script became our most valuable tool. This script connected directly to the PostgreSQL database, completely bypassing our Flask application, Gunicorn (the server), and SQLAlchemy (the database library).
The script gave us the "smoking gun":
The moment you approved the job, the script's output changed.
This proved, with 100% certainty, that the UPDATE command was successful and the data in the database itself was instantly correct.
This allowed us to narrow the problem down with pinpoint accuracy. The issue is not the database; it's the application's view of the database. The API that reads the job list was looking at an outdated snapshot of the data.
The Root Cause: A Tale of Two Workers and Stale Snapshots
To understand the "why," we need to look at three concepts: Gunicorn Workers, Database Transactions, and SQLAlchemy Sessions.
Gunicorn Workers: In production (and our Docker environment), the application isn't just one single program. The Gunicorn server runs multiple copies of our Flask app at the same time to handle multiple user requests simultaneously. These are called "workers." A request to get the job list might go to Worker #1, while the request to approve a job might go to Worker #2.
Database Transactions (The Snapshot): When you interact with a database, you are doing so within a "transaction." A key feature of a transaction is that it gives you a consistent, stable "snapshot" of the database from the moment the transaction began. It's like taking a photocopy of the database. Even if someone else changes the real data, you continue to see what's on your photocopy until you start a new transaction (get a new photocopy).
SQLAlchemy Sessions (The Conversation): In our code, db.session is our "conversation" with the database. When a request comes into a worker, it starts a session and that session begins a transaction (takes a photocopy). By default, that session can stay open for a while on that worker to efficiently handle more requests.
Here is the exact sequence of events that causes our bug:
Request A (Get Jobs): Your browser asks for the list of UPLOADED jobs. The request is assigned to Gunicorn Worker #1.
Snapshot A is created: Worker #1 starts a database session and a transaction. It gets a "snapshot" of the database where there are 2 UPLOADED jobs. It sends this list to your browser. The transaction on Worker #1 remains open.
Request B (Approve Job): You click "Approve." This is a new request. It is assigned to Gunicorn Worker #2.
Worker #2 Acts: Worker #2 starts its own session, updates the job status from UPLOADED to PENDING, and COMMITs its transaction. The change is now permanent in the database.
Request C (Get Jobs again): Your browser, after the approval, immediately asks for the list of UPLOADED jobs again. This request happens to land back on Gunicorn Worker #1.
The Stale Read: Worker #1's original transaction is still open. Its "snapshot" of the database is from before the approval. It looks at its old snapshot, sees 2 UPLOADED jobs, and sends this stale data back to your browser.
This continues until Worker #1's transaction finally times out or is recycled, at which point it gets a new, fresh snapshot and finally sees the change. This is the source of the ~45-second delay.
Why My Fixes Didn't Work (and Why Your Revert Was Insightful)
You reverted my change from db.session.remove() back to db.session.expire_all(). This was a good instinct, because it's important to understand the difference.
db.session.expire_all(): This is a gentle approach. It tells the session, "The Python objects you're holding might be out of date. Next time I ask for them, please re-fetch them from the database." However, this re-fetch happens inside the same old, stale transaction. It's like re-reading the outdated photocopy. It doesn't solve the problem.
db.session.remove(): This is a much more forceful approach. It tells the worker, "Throw your entire current session and transaction in the garbage." The very next time any code asks for db.session, SQLAlchemy is forced to create a brand new session, which starts a brand new transaction, which takes a brand new, up-to-date snapshot of the database.
This db.session.remove() command is the correct and standard solution in Flask/SQLAlchemy for this exact problem. It explicitly ensures that any GET request for a list of data is never served from a potentially stale transaction. By placing it at the start of list_jobs and get_job_counts, we guarantee that these functions always report the absolute latest state of the database.

Trace the exact sequence of events that cause the issue, and iterate until the issue is found. Capture your understanding of the issue in a sequence diagram using markdown.

Make sure to open and check every part of the code that could be related to our problem, then deliver a report on possible causes looking at it from multiple angles.

Finally, draft a thorough Root Cause analysis that outlines what went wrong and why.