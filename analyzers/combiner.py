def combiner(data):
    game_name = ""
    game_id = []
    in_queue = 0
    average_daily = 0
    verified_daily = 0
    verifier_analyzed = 0
    verifier_stats = []
    background_image = data[0]['background_image']
    other_found = False
    other = {
        "name": "Other",
        "runs": 0,
        "rejected_runs": 0,
        "length": [],
        "color": "#000000",
        "has_pfp": False,
        'pfp_uri': None,
    }
    other_list = []
    for x in data:
        game_name += x['game_name'] + ", "
        game_id.append(x['game_id'])
        in_queue += x['in_queue']
        average_daily += x['average_daily']
        verified_daily += x['verified_daily']
        verifier_analyzed += x['verifier_analyzed']
        other_list += x['other_list']

        for y in x["verifier_stats"]:
            found = False
            if y['name'] == "Other":
                other_found = True
                other['runs'] += y['runs']
                other['length'] += y['length']
                continue
            for z in verifier_stats:
                if z['id'] == y['id']:
                    z['runs'] += y['runs']
                    z['length'] += y['length']
                    found = True
                    break
            if not found:
                verifier_stats.append(y)
    average_daily = round(average_daily, 2)
    verified_daily = round(verified_daily, 2)
    if other_found:
        verifier_stats.append(other)
    game_id_str = ""
    for x in game_id:
        game_id_str += f"{x},"
    
    return {
        "game_name": game_name[:-2],
        "background_image": background_image,
        "game_id": game_id_str[:-1],
        "in_queue": in_queue,
        "average_daily": average_daily,
        "verified_daily": verified_daily,
        "verifier_analyzed": verifier_analyzed,
        "verifier_stats": verifier_stats,
        "other_list": other_list
    }