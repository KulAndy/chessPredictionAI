SETTINGS = {
    'splitted_pgns_dir': 'splitted_pgns2',
    'ignored_players': ['?', '*', 'N, N', 'N, N.'],
    'analyzed_games': 'analyzed_games',
    'mongo': {
        'host': "localhost",
        'port': 27017,
        'database': 'ai_data_set',
        'collection': 'ai_data_set2',
    },
    'model_dir': 'saved_model',
    'API': {
        'search_player': 'https://api.bazaszachowa.smallhost.pl/search_player/',  # /name
        'search_games': 'https://api.bazaszachowa.smallhost.pl/search_player_opening_game/',  # /name/color
    },
    'tensorboard_log_dir': 'logs/'
}
