This is a project that is currently a work in progress.It works right now for 22 tournaments. All the tournament data and images used come from this site: https://lol.fandom.com/wiki/League_of_Legends_Esports_Wiki. In order for the program to work the user must run the startdata.py file to create the database tables. Comment out the drop table if the database file is empty. Then run the scraper.py file to populate the tables. This scrapes the website for the tournaments provided and populates the tables with the data from all of those games. Then you can run the flask application in a virtual environment. To install flask go here: https://flask.palletsprojects.com/en/3.0.x/installation/. You can start the application with flask --app flaskr run --debug. I will update the html to make it more pleasant, but for now it works as it will randomly select one game and paste the bans and pick images on the page. I might also add team logos instead of text for the team names. The tournament is entered first through a select field. The select fields were created using chosen jquery plugin. Then if the user gets the tournament correct they are redirected to a select field for the game played. They must make sure the first team mentioned is the blue team in this game. If the user inputs/selects 5 wrong values it redirects to a page that prints the correct answser and that the user got it wrong. If they get it all right it instead redirects to a page that prints all the correct info and a congratulatory message. Deployed version of the site is found here: https://loldraftle.com/

**Update: 8/15/2024**
I created a new feature where the user input for year, tournament, and time of year would be printed to the page after every user guess either marked green for correct, or red if incorrect. Then if the user guessed the tournament correctly it would then print to the page
the user's team inputs, either marked green for correct, yellow if correct team but on wrong side, or red if incorrect team.

**Update: 9/02/2024**
I added an attempt history graph using Chart.js. This would display a bar graph at the end screen for the user to view their attempt history by using new attempt variables in local storage. I also had to update the scraper file as some html was changed on leaguepedia which is where I get the match information. I also added a new SQL table called checkid which is used in case the random id is the same two days in a row. This would cause all users to be locked out another day because the id changing is what resets the game every day. In the future I could use this to ensure a different match is called every single time, but for now I feel repeats eventually are ok.

**Update: 9/09/2024**
Added higher lower classes for guessed years so users can more easily guess the tournament. Also added more tournaments to the scraper file and the database.

**Update: 9/30/2024**
Revamped site design and uploaded new images for champion picks using riot's Data Dragon site's resources. Improved the format and readability of the html pages by using flex containers. Also utlized sessions for counter since global variable was not thread safe.

**Update: 10/20/2026**
The game is now a single page. Guesses are sent to `/api/guess` and `/api/hint` with fetch and the page updates in place, including the end screen (stats, chart, VOD and a countdown to the next match).
- The server keeps each player's progress in the session, so it enforces the daily lock: a finished game stays finished on refresh, and `/correct` / `/incorrect` just redirect to `/`. The answer and player names are no longer in the page source until they are revealed.
- The daily match is picked from the date (a seeded shuffle that goes through every match before repeating), so it no longer depends on restarting the server and the `checkid` table isn't used.
- Repeating a guess no longer costs an attempt. Stats are stored in one `lolStats` localStorage key (old stats are migrated automatically).

**Update: daily games per region**
The site now opens on a home page with six daily games: LCK (with OGN), LPL, LEC, LCS (with LTA / LTA North), International (Worlds, MSI and First Stand) and Worlds only. Each game picks its own match every day. You guess the year (higher/lower arrows), then the blue side and red side teams from the teams that played in that region that year. Every game has its own 5 attempts, hints and stats, and the home page shows which games you've won, lost or started. Pages are `/play/<game>`, e.g. `/play/lck`, and the API is `/api/<game>/guess` and `/api/<game>/hint`. The game list is `GAMES` in `flaskr/game.py`.

**Draft order**
The scraped match history lists picks by role, so the order teams picked in comes from a second source. After scraping, run `python -m flaskr.draftorder`: it reads Leaguepedia's picks-and-bans data (2017 onward) and saves each game's pick order in a `pickOrder` table, matching games on the champions each side picked. Games that have it show B1–B5 / R1–R5 badges and a Draft order / Roles switch; older games keep the role layout. It skips games it has already done, so re-run it after adding tournaments. The tournament list both scripts use is in `flaskr/tournaments.py`.

**Logos and VODs**
- Team logos: run `python -m flaskr.logos` from the project root after scraping new tournaments. It downloads each team's "logo square" image from Leaguepedia (128px) into `flaskr/static/images/teams/` and skips teams it already has. They appear in the team boxes once a team is guessed and on the end screen.
- League logos for the home page cards: add `lck`, `lpl`, `lec`, `lcs`, `international` and `worlds` images (png, svg or webp) to `flaskr/static/images/leagues/`. A card without one just shows the name.
- Logos are trademarks of Riot Games and the teams, used here under Riot's fan content policy for a free, non-commercial project.
- The end screen shows the VOD as a click-to-play thumbnail with a "Watch on YouTube" link underneath. Each video is checked with YouTube once per server run, and deleted or private videos and old Twitch links show "No VOD available".
