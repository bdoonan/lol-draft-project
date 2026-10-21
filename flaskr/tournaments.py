#the tournaments in the database and their leaguepedia match history pages
#shared by scraper.py (to scrape them) and draftorder.py (to look up their pick order)


def tournament_urls(start_year, end_year):
    """tournament name -> leaguepedia match history url, in the order they happen each year"""
    urls = {}

    def add(name, url):
        urls[name] = url

    for i in range(start_year, end_year + 1):
        # Winter playoffs
        if i > 2024:
            add(f"{i} LTA Winter Playoffs", f"https://lol.fandom.com/wiki/LTA/{i}_Season/Split_1_Playoffs/Match_History")
            add(f"{i} LCK Cup Playoffs", f"https://lol.fandom.com/wiki/LCK/{i}_Season/Cup/Match_History")
            add(f"{i} LPL Winter Playoffs", f"https://lol.fandom.com/wiki/LPL/{i}_Season/Split_1_Playoffs/Match_History")

        # LEC Winter Playoffs
        if i > 2022:
            add(f"{i} LEC Winter Playoffs", f"https://lol.fandom.com/wiki/LEC/{i}_Season/Winter_Playoffs/Match_History")

        # OGN Winter Playoffs (special cases)
        if i == 2013:
            add(f"{i} OGN Winter Playoffs", "https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2013+Winter&MHG%5Bstartdate%5D=2012-12-25&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=")
        if i == 2014:
            add(f"{i} OGN Winter Playoffs", "https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2014+Winter&MHG%5Bstartdate%5D=2013-12-25&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=")

        # First Stand
        if i > 2024:
            add(f"{i} First Stand", f"https://lol.fandom.com/wiki/{i}_First_Stand/Match_History")

        # Spring playoffs
        # LCS Spring
        if i == 2013:
            add(f"{i} LCS Spring Playoffs", f"https://lol.fandom.com/wiki/NA_LCS/Season_{i%10}/Spring_Playoffs/Match_History")
        elif i < 2019:
            add(f"{i} LCS Spring Playoffs", f"https://lol.fandom.com/wiki/NA_LCS/{i}_Season/Spring_Playoffs/Match_History")
        elif i == 2021:
            add(f"{i} LCS Spring Playoffs", f"https://lol.fandom.com/wiki/LCS/{i}_Season/Mid-Season_Showdown/Match_History")
        elif i < 2025:
            add(f"{i} LCS Spring Playoffs", f"https://lol.fandom.com/wiki/LCS/{i}_Season/Spring_Playoffs/Match_History")
        else:
            add(f"{i} LTA_North Spring Playoffs", f"https://lol.fandom.com/wiki/LTA_North/{i}_Season/Split_2_Playoffs/Match_History")

        # LEC Spring
        if i == 2013:
            add(f"{i} LEC Spring Playoffs", f"https://lol.fandom.com/wiki/EU_LCS/Season_{i%10}/Spring_Playoffs/Match_History")
        elif i < 2019:
            add(f"{i} LEC Spring Playoffs", f"https://lol.fandom.com/wiki/EU_LCS/{i}_Season/Spring_Playoffs/Match_History")
        else:
            add(f"{i} LEC Spring Playoffs", f"https://lol.fandom.com/wiki/LEC/{i}_Season/Spring_Playoffs/Match_History")

        # LCK/OGN Spring
        if i == 2013:
            add(f"{i} OGN Spring Playoffs", "https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2013+Spring&MHG%5Bstartdate%5D=2013-05-08&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=")
        elif i == 2014:
            add(f"{i} OGN Spring Playoffs", "https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2014+Spring&MHG%5Bstartdate%5D=2014-04-16&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=")
        elif i < 2016:
            add(f"{i} LCK Spring Playoffs", f"https://lol.fandom.com/wiki/Champions/{i}_Season/Spring_Playoffs/Match_History")
        elif i < 2025:
            add(f"{i} LCK Spring Playoffs", f"https://lol.fandom.com/wiki/LCK/{i}_Season/Spring_Playoffs/Match_History")
        else:
            add(f"{i} LCK Road_to MSI", f"https://lol.fandom.com/wiki/LCK/{i}_Season/Road_to_MSI/Match_History")

        # LPL Spring
        if i < 2025:
            add(f"{i} LPL Spring Playoffs", f"https://lol.fandom.com/wiki/LPL/{i}_Season/Spring_Playoffs/Match_History")
        else:
            add(f"{i} LPL Spring Playoffs", f"https://lol.fandom.com/wiki/LPL/{i}_Season/Split_2_Playoffs/Match_History")

        # MSI
        if 2016 < i < 2020:
            add(f"{i} MSI", f"https://lol.fandom.com/wiki/{i}_Mid-Season_Invitational/Main_Event/Match_History")
        else:
            add(f"{i} MSI", f"https://lol.fandom.com/wiki/{i}_Mid-Season_Invitational/Match_History")

        # Summer playoffs
        # LCS Summer
        if i == 2013:
            add(f"{i} LCS Summer Playoffs", f"https://lol.fandom.com/wiki/NA_LCS/Season_{i%10}/Summer_Playoffs/Match_History")
        elif i < 2019:
            add(f"{i} LCS Summer Playoffs", f"https://lol.fandom.com/wiki/NA_LCS/{i}_Season/Summer_Playoffs/Match_History")
        elif i < 2021:
            add(f"{i} LCS Summer Playoffs", f"https://lol.fandom.com/wiki/LCS/{i}_Season/Summer_Playoffs/Match_History")
        else:
            add(f"{i} LCS Summer Playoffs", f"https://lol.fandom.com/wiki/LCS/{i}_Season/Championship/Match_History")

        # LEC Summer
        if i == 2013:
            add(f"{i} LEC Summer Playoffs", f"https://lol.fandom.com/wiki/EU_LCS/Season_{i%10}/Summer_Playoffs/Match_History")
        elif i < 2019:
            add(f"{i} LEC Summer Playoffs", f"https://lol.fandom.com/wiki/EU_LCS/{i}_Season/Summer_Playoffs/Match_History")
        else:
            add(f"{i} LEC Summer Playoffs", f"https://lol.fandom.com/wiki/LEC/{i}_Season/Summer_Playoffs/Match_History")

        # LCK/OGN Summer
        if i == 2013:
            add(f"{i} OGN Summer Playoffs", "https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2013+Summer&MHG%5Bstartdate%5D=2013-08-07&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=")
        elif i == 2014:
            add(f"{i} OGN Summer Playoffs", "https://lol.fandom.com/wiki/Special:RunQuery/MatchHistoryGame?MHG%5Btournament%5D=Champions+2014+Summer&MHG%5Bstartdate%5D=2014-07-16&MHG%5Bpreload%5D=Tournament&MHG%5Bspl%5D=yes&_run=")
        elif i < 2016:
            add(f"{i} LCK Summer Playoffs", f"https://lol.fandom.com/wiki/Champions/{i}_Season/Summer_Playoffs/Match_History")
        elif i < 2025:
            add(f"{i} LCK Summer Playoffs", f"https://lol.fandom.com/wiki/LCK/{i}_Season/Summer_Playoffs/Match_History")
        else:
            add(f"{i} LCK Summer Playoffs", f"https://lol.fandom.com/wiki/LCK/{i}_Season/Season_Playoffs/Match_History")

        # LPL Summer
        if i < 2025:
            add(f"{i} LPL Summer Playoffs", f"https://lol.fandom.com/wiki/LPL/{i}_Season/Summer_Playoffs/Match_History")
        else:
            add(f"{i} LPL Summer Playoffs", f"https://lol.fandom.com/wiki/LPL/{i}_Season/Grand_Finals/Match_History")

        # LEC Season Finals
        add(f"{i} LEC Season Finals", f"https://lol.fandom.com/wiki/LEC/{i}_Season/Season_Finals/Match_History")

        # Regional Finals
        # LCS Regional
        if i < 2019:
            add(f"{i} LCS Regional Finals", f"https://lol.fandom.com/wiki/NA_LCS/{i}_Season/Regional_Finals/Match_History")
        else:
            add(f"{i} LCS Regional Finals", f"https://lol.fandom.com/wiki/LCS/{i}_Season/Regional_Finals/Match_History")

        # LEC Regional
        if i < 2019:
            add(f"{i} LEC Regional Finals", f"https://lol.fandom.com/wiki/EU_LCS/{i}_Season/Regional_Finals/Match_History")
        else:
            add(f"{i} LEC Regional Finals", f"https://lol.fandom.com/wiki/LEC/{i}_Season/Regional_Finals/Match_History")

        # LPL Regional
        add(f"{i} LPL Regional Finals", f"https://lol.fandom.com/wiki/LPL/{i}_Season/Regional_Finals/Match_History")

        # LCK/OGN Regional
        if i == 2013:
            add(f"{i} OGN Regional Finals", f"https://lol.fandom.com/wiki/Season_{i%10}_Korea_Regional_Finals/Match_History")
        elif i < 2015:
            add(f"{i} OGN Regional Finals", f"https://lol.fandom.com/wiki/{i}_Season_Korea_Regional_Finals/Match_History")
        elif i < 2016:
            add(f"{i} LCK Regional Finals", f"https://lol.fandom.com/wiki/{i}_Season_Korea_Regional_Finals/Match_History")
        else:
            add(f"{i} LCK Regional Finals", f"https://lol.fandom.com/wiki/LCK/{i}_Season/Regional_Finals/Match_History")

        # Worlds
        if i < 2014:
            add(f"{i} Worlds", f"https://lol.fandom.com/wiki/Season_{i%10}_World_Championship/Match_History")
        elif i > 2016:
            add(f"{i} Worlds", f"https://lol.fandom.com/wiki/{i}_Season_World_Championship/Main_Event/Match_History")
        else:
            add(f"{i} Worlds", f"https://lol.fandom.com/wiki/{i}_Season_World_Championship/Match_History")
    return urls


def overview_page(url):
    """'https://lol.fandom.com/wiki/LCK/2023_Season/Summer_Playoffs/Match_History' -> 'LCK/2023 Season/Summer Playoffs'
    None for the special query urls used for some old OGN events"""
    prefix, suffix = 'https://lol.fandom.com/wiki/', '/Match_History'
    if not url.startswith(prefix) or not url.endswith(suffix) or 'Special:' in url:
        return None
    return url[len(prefix):-len(suffix)].replace('_', ' ')
