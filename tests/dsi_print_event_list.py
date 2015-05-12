import dsi_scrape

event_name = "USA_Dance_National_Dancesport_Championship_27707"

events = dsi_scrape.event_list(event_name)

for e in events:
    print(e)