# Deploying on PythonAnywhere

The live site only reads `test.db`. Every player's progress is in their session cookie and their stats are in their browser, so the server has no database to run and nothing to lose on a redeploy. A paid plan (Hacker, about $5/month) is needed for the custom domain and HTTPS.

## One-time setup

1. **Code and packages** (Bash console):
   ```
   git clone <your repo> ~/lol-draft-project
   cd ~/lol-draft-project
   mkvirtualenv draftle --python=python3.11
   pip install -r requirements.txt
   ```
   `test.db` and `flaskr/static/images/` must be in the repo, or uploaded to the same paths.

2. **Secret key.** Generate one locally with `python -c "import secrets; print(secrets.token_hex(32))"`. The app refuses to start in production without it.

3. **Web tab:**
   - Source code: `/home/<user>/lol-draft-project`
   - Virtualenv: `/home/<user>/.virtualenvs/draftle`
   - WSGI configuration file, replacing its contents:
     ```python
     import os, sys
     path = '/home/<user>/lol-draft-project'
     if path not in sys.path:
         sys.path.insert(0, path)
     os.environ['SECRET_KEY'] = '<the value from step 2>'
     from flaskr import create_app
     application = create_app()
     ```
   - Static files: URL `/static/` → directory `/home/<user>/lol-draft-project/flaskr/static`. PythonAnywhere then serves the images itself, without going through Flask.
   - Security: turn on **Force HTTPS**. The session cookie is marked secure, so it is only sent over https.

4. **Custom domain:**
   - Add the web app under your domain (e.g. `www.loldraftle.com`).
   - Point a CNAME record at the `webapp-XXXX.pythonanywhere.com` address shown on the Web tab.
   - Enable the free Let's Encrypt certificate.
   - To make the bare `loldraftle.com` work too, set your registrar's domain forwarding to `https://www.loldraftle.com`.

## Updating the data

On your own machine (needs `pip install -r requirements-scripts.txt`):
```
python flaskr/scraper.py        # after adding the new tournaments to flaskr/tournaments.py
python -m flaskr.draftorder     # pick order for the new games
python -m flaskr.logos          # logos for any new teams
python -m pytest tests
git add test.db flaskr/static/images && git commit -m "Add <tournament>" && git push
```
Then on PythonAnywhere: `cd ~/lol-draft-project && git pull`, and press **Reload** on the Web tab.

Adding games changes the daily rotation from the next day on, so it is best to update just after midnight UTC.

## Good to know

- **The daily matches change at midnight UTC.** `FORCE_DAY` is only for testing; don't set it on the server.
- **Free accounts can only reach allowlisted websites.** If the YouTube check that hides deleted VODs can't connect, the VOD is simply shown as normal.
- **Static files are cached by browsers for a week.** If you replace an image under the same name (e.g. a new league logo), returning players may see the old one for a few days. Giving the file a new name avoids that.
- **If traffic ever spikes,** putting the domain behind Cloudflare's free plan caches the images and static files at the edge, with no change to the app.
