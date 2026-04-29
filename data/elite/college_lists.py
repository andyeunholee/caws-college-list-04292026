# college_lists.py
# US News 2024-2025 Rankings
# school name + state are used to look up College Scorecard data

NATIONAL_UNIVERSITIES = [
    # ── Top 10 ──────────────────────────────────────────────────────────────
    {"name": "Princeton University",                          "state": "NJ"},   # #1
    {"name": "Massachusetts Institute of Technology",         "state": "MA"},   # #2
    {"name": "Harvard University",                            "state": "MA", "test_policy": "Required"},   # #3
    {"name": "Stanford University",                           "state": "CA", "test_policy": "Required"},   # #3
    {"name": "Yale University",                               "state": "CT", "test_policy": "Required"},   # #5
    {"name": "University of Chicago",                         "state": "IL"},   # #6
    {"name": "Johns Hopkins University",                      "state": "MD", "test_policy": "Required"},   # #7
    {"name": "University of Pennsylvania",                    "state": "PA", "test_policy": "Required"},   # #7
    {"name": "California Institute of Technology",            "state": "CA", "test_policy": "Required"},   # #9
    {"name": "Duke University",                               "state": "NC"},   # #9
    # ── 11–20 ───────────────────────────────────────────────────────────────
    {"name": "Dartmouth College",                             "state": "NH"},   # #11
    {"name": "Northwestern University",                       "state": "IL", "test_policy": "Required"},   # #11
    {"name": "Brown University",                              "state": "RI", "test_policy": "Required"},   # #13
    {"name": "Vanderbilt University",                         "state": "TN"},   # #13
    {"name": "Columbia University",                           "state": "NY"},   # #13
    {"name": "Cornell University",                            "state": "NY", "test_policy": "Required"},   # #16
    {"name": "Rice University",                               "state": "TX"},   # #17
    {"name": "Washington University in St. Louis",            "state": "MO"},   # #18
    {"name": "University of Notre Dame",                      "state": "IN"},   # #19
    {"name": "University of California, Los Angeles",         "state": "CA"},   # #20
    # ── 21–30 ───────────────────────────────────────────────────────────────
    {"name": "Emory University",                              "state": "GA"},   # #21
    {"name": "University of California, Berkeley",            "state": "CA"},   # #22
    {"name": "Georgetown University",                         "state": "DC"},   # #23
    {"name": "Carnegie Mellon University",                    "state": "PA"},   # #24
    {"name": "University of Michigan-Ann Arbor",              "state": "MI"},   # #25
    {"name": "University of North Carolina at Chapel Hill",   "state": "NC"},   # #26
    {"name": "University of Virginia",                        "state": "VA"},   # #27
    {"name": "University of Southern California",             "state": "CA"},   # #27
    {"name": "Tufts University",                              "state": "MA"},   # #29
    {"name": "New York University",                           "state": "NY"},   # #30
    # ── 31–40 ───────────────────────────────────────────────────────────────
    {"name": "University of California, Santa Barbara",       "state": "CA"},   # #30
    {"name": "University of Florida",                         "state": "FL"},   # #32
    {"name": "Georgia Institute of Technology",               "state": "GA"},   # #33
    {"name": "University of Rochester",                       "state": "NY"},   # #33
    {"name": "Boston College",                                "state": "MA"},   # #35
    {"name": "Wake Forest University",                        "state": "NC"},   # #35
    {"name": "Lehigh University",                             "state": "PA"},   # #37
    {"name": "Northeastern University",                       "state": "MA"},   # #49 (tied)
    {"name": "William & Mary",                                "state": "VA"},   # #44 (tied)
    {"name": "University of Georgia",                         "state": "GA"},   # #44 (tied)
    # ── 41–50 ───────────────────────────────────────────────────────────────
    {"name": "University of Wisconsin-Madison",               "state": "WI"},   # #41
    {"name": "Tulane University",                             "state": "LA"},   # #42
    {"name": "University of Illinois Urbana-Champaign",       "state": "IL"},   # #43
    {"name": "Purdue University",                             "state": "IN"},   # #44
    {"name": "Ohio State University",                         "state": "OH"},   # #45
    {"name": "Pennsylvania State University",                 "state": "PA"},   # #46
    {"name": "Texas A&M University",                          "state": "TX"},   # #47
    {"name": "University of Texas at Austin",                 "state": "TX"},   # #48
    {"name": "Indiana University Bloomington",                "state": "IN"},   # #49
    {"name": "University of Washington",                      "state": "WA"},   # #50
    # ── 51–60 ───────────────────────────────────────────────────────────────
    {"name": "Michigan State University",                     "state": "MI"},   # #51 (tied)
    {"name": "Virginia Tech",                                 "state": "VA"},   # #51 (tied)
    {"name": "Case Western Reserve University",               "state": "OH"},   # #51 (tied)
    {"name": "University of Maryland, College Park",          "state": "MD"},   # #54 (tied)
    {"name": "Boston University",                             "state": "MA"},   # #54 (tied)
    {"name": "Rensselaer Polytechnic Institute",              "state": "NY"},   # ~#55
    {"name": "University of Pittsburgh",                      "state": "PA"},   # #56
    {"name": "Florida State University",                      "state": "FL"},   # #57
    {"name": "Villanova University",                          "state": "PA"},   # #58 (tied)
    {"name": "Stony Brook University",                        "state": "NY"},   # #58 (tied)
    # ── 61–70 ───────────────────────────────────────────────────────────────
    {"name": "University of Massachusetts Amherst",           "state": "MA"},   # #58 (tied) ★ added
    {"name": "North Carolina State University",               "state": "NC"},   # #58 (tied) ★ added
    {"name": "University of California, Merced",              "state": "CA"},   # #58 (tied) ★ added
    {"name": "Brandeis University",                           "state": "MA"},   # #63 (tied) ★ added
    {"name": "George Washington University",                  "state": "DC"},   # #63 (tied)
    {"name": "Fordham University",                            "state": "NY"},   # #63 (tied)
    {"name": "University of Miami",                           "state": "FL"},   # #63 (tied)
    {"name": "Syracuse University",                           "state": "NY"},   # #63 (tied)
    {"name": "Stevens Institute of Technology",               "state": "NJ"},   # #74 (tied)
    {"name": "University of Connecticut",                     "state": "CT"},   # ~#65
    # ── 71–80 ───────────────────────────────────────────────────────────────
    {"name": "Clemson University",                            "state": "SC"},   # ~#66
    {"name": "University of California, Davis",               "state": "CA"},   # ~#67
    {"name": "University of California, San Diego",           "state": "CA"},   # ~#68
    {"name": "University of California, Irvine",              "state": "CA"},   # ~#69
    {"name": "New Jersey Institute of Technology",            "state": "NJ"},   # #74 (tied) ★ added
    {"name": "Drexel University",                             "state": "PA"},   # #74 (tied)
    {"name": "Colorado School of Mines",                      "state": "CO"},   # #74 (tied)
    {"name": "Santa Clara University",                        "state": "CA"},   # ~#74
    {"name": "Marquette University",                          "state": "WI"},   # #88 (tied)
    {"name": "Pepperdine University",                         "state": "CA"},   # #84 (tied)
    # ── 81–90 ───────────────────────────────────────────────────────────────
    {"name": "University of California, Santa Cruz",          "state": "CA"},   # #84 (tied) ★ added
    {"name": "Worcester Polytechnic Institute",               "state": "MA"},   # #84 (tied)
    {"name": "Howard University",                             "state": "DC"},   # #86 (tied)
    {"name": "University of Delaware",                        "state": "DE"},   # #86 (tied)
    {"name": "Rochester Institute of Technology",             "state": "NY"},   # #88 (tied) ★ added
    {"name": "Southern Methodist University",                 "state": "TX"},   # #88 (tied) ★ added
    {"name": "University of South Florida",                   "state": "FL"},   # #88 (tied) ★ added
    {"name": "American University",                           "state": "DC"},   # #91 (tied)
    {"name": "Loyola Marymount University",                   "state": "CA"},   # #91 (tied) ★ added
    {"name": "University of Denver",                          "state": "CO"},   # ~#91
    # ── 91–103 (ties extend beyond 100) ─────────────────────────────────────
    {"name": "Baylor University",                             "state": "TX"},   # ~#91
    {"name": "Loyola University Chicago",                     "state": "IL"},   # ~#91
    {"name": "Texas Christian University",                    "state": "TX"},   # ~#91
    {"name": "University of Minnesota Twin Cities",           "state": "MN"},   # ~#91
    {"name": "Rutgers University-New Brunswick",              "state": "NJ"},   # ~#95
    {"name": "University of Iowa",                            "state": "IA"},   # #98 (tied)
    {"name": "University of Colorado Boulder",                "state": "CO"},   # ~#97
    {"name": "University at Buffalo",                         "state": "NY"},   # ~#97
    {"name": "University of Utah",                            "state": "UT"},   # ~#97
    {"name": "University of Tennessee",                       "state": "TN"},   # ~#97
    {"name": "Gonzaga University",                            "state": "WA"},   # #98 (tied) ★ added
    {"name": "Florida International University",              "state": "FL"},   # #98 (tied) ★ added
    {"name": "Yeshiva University",                            "state": "NY"},   # ~#100
]

LIBERAL_ARTS_COLLEGES = [
    {"name": "Williams College",                              "state": "MA"},
    {"name": "Amherst College",                               "state": "MA"},
    {"name": "Swarthmore College",                            "state": "PA"},
    {"name": "Pomona College",                                "state": "CA"},
    {"name": "Wellesley College",                             "state": "MA"},
    {"name": "Bowdoin College",                               "state": "ME"},
    {"name": "Carleton College",                              "state": "MN"},
    {"name": "Middlebury College",                            "state": "VT"},
    {"name": "Claremont McKenna College",                     "state": "CA"},
    {"name": "Davidson College",                              "state": "NC"},
    {"name": "Washington and Lee University",                 "state": "VA"},
    {"name": "Colby College",                                 "state": "ME"},
    {"name": "Colgate University",                            "state": "NY"},
    {"name": "Hamilton College",                              "state": "NY"},
    {"name": "Harvey Mudd College",                           "state": "CA"},
    {"name": "Vassar College",                                "state": "NY"},
    {"name": "Smith College",                                 "state": "MA"},
    {"name": "United States Naval Academy",                   "state": "MD"},
    {"name": "United States Military Academy",                "state": "NY"},
    {"name": "Haverford College",                             "state": "PA"},
    {"name": "Barnard College",                               "state": "NY"},
    {"name": "College of the Holy Cross",                     "state": "MA"},
    {"name": "Bates College",                                 "state": "ME"},
    {"name": "Grinnell College",                              "state": "IA"},
    {"name": "Occidental College",                            "state": "CA"},
    {"name": "Kenyon College",                                "state": "OH"},
    {"name": "Colorado College",                              "state": "CO"},
    {"name": "Mount Holyoke College",                         "state": "MA"},
    {"name": "Trinity College",                               "state": "CT"},
    {"name": "University of Richmond",                        "state": "VA"},
    {"name": "Furman University",                             "state": "SC"},
    {"name": "Denison University",                            "state": "OH"},
    {"name": "Dickinson College",                             "state": "PA"},
    {"name": "Scripps College",                               "state": "CA"},
    {"name": "St. Olaf College",                              "state": "MN"},
    {"name": "Bryn Mawr College",                             "state": "PA"},
    {"name": "Bucknell University",                           "state": "PA"},
    {"name": "Lafayette College",                             "state": "PA"},
    {"name": "Skidmore College",                              "state": "NY"},
    {"name": "Union College",                                 "state": "NY"},
    {"name": "Whitman College",                               "state": "WA"},
    {"name": "Oberlin College",                               "state": "OH"},
    {"name": "Reed College",                                  "state": "OR"},
    {"name": "Macalester College",                            "state": "MN"},
    {"name": "Connecticut College",                           "state": "CT"},
    {"name": "Muhlenberg College",                            "state": "PA"},
    {"name": "Franklin & Marshall College",                   "state": "PA"},
    {"name": "Gettysburg College",                            "state": "PA"},
    {"name": "Lawrence University",                           "state": "WI"},
    {"name": "Rhodes College",                                "state": "TN"},
    {"name": "DePauw University",                             "state": "IN"},
    {"name": "Wabash College",                                "state": "IN"},
    {"name": "Centre College",                                "state": "KY"},
    {"name": "Allegheny College",                             "state": "PA"},
    {"name": "Earlham College",                               "state": "IN"},
    {"name": "Wofford College",                               "state": "SC"},
    {"name": "Hobart and William Smith Colleges",             "state": "NY"},
    {"name": "Sewanee: The University of the South",          "state": "TN"},
    {"name": "Augustana College",                             "state": "IL"},
    {"name": "College of Wooster",                            "state": "OH"},
    {"name": "Juniata College",                               "state": "PA"},
    {"name": "Beloit College",                                "state": "WI"},
    {"name": "Gustavus Adolphus College",                     "state": "MN"},
    {"name": "Ohio Wesleyan University",                      "state": "OH"},
    {"name": "Luther College",                                "state": "IA"},
    {"name": "Hope College",                                  "state": "MI"},
    {"name": "Kalamazoo College",                             "state": "MI"},
    {"name": "Hanover College",                               "state": "IN"},
    {"name": "Ripon College",                                 "state": "WI"},
    {"name": "Austin College",                                "state": "TX"},
    {"name": "Agnes Scott College",                           "state": "GA"},
    {"name": "Berea College",                                 "state": "KY"},
    {"name": "University of Puget Sound",                     "state": "WA"},
    {"name": "Hendrix College",                               "state": "AR"},
    {"name": "St. John's College",                            "state": "MD"},
    {"name": "Transylvania University",                       "state": "KY"},
    {"name": "Pitzer College",                                "state": "CA"},
    {"name": "Sarah Lawrence College",                        "state": "NY"},
    {"name": "Illinois Wesleyan University",                  "state": "IL"},
    {"name": "Randolph-Macon College",                        "state": "VA"},
    {"name": "Hampden-Sydney College",                        "state": "VA"},
    {"name": "Morehouse College",                             "state": "GA"},
    {"name": "Spelman College",                               "state": "GA"},
    {"name": "Knox College",                                  "state": "IL"},
    {"name": "Lake Forest College",                           "state": "IL"},
    {"name": "Alma College",                                  "state": "MI"},
    {"name": "Concordia College",                             "state": "MN"},
    {"name": "Willamette University",                         "state": "OR"},
    {"name": "Westminster College",                           "state": "MO"},
    {"name": "Wittenberg University",                         "state": "OH"},
    {"name": "Millsaps College",                              "state": "MS"},
    {"name": "Gordon College",                                "state": "MA"},
    {"name": "Hiram College",                                 "state": "OH"},
    {"name": "Pacific Lutheran University",                   "state": "WA"},
    {"name": "Covenant College",                              "state": "GA"},
    {"name": "Monmouth College",                              "state": "IL"},
    {"name": "Drew University",                               "state": "NJ"},
    {"name": "Muskingum University",                          "state": "OH"},
    {"name": "Albion College",                                "state": "MI"},
]
