from dataclasses import dataclass


@dataclass
class Rank:
    rank_id : int 
    name : str
    x : float
    tasks : int
    referral : int
    
    
description = [
    ("Бронза", 1.0, 1, 0),
    ("Серебро", 1.1, 50, 10),
    ("Золото", 1.2, 100, 20),
    ("Платина", 1.3, 200, 50),
    ("Алмаз", 1.4, 300, 100),
    ("Корона", 1.5, 400, 150),
    ("Ас", 1.6, 500, 250),
    ("Завоеватель", 2.0, 1000, 500)
]

class RankCollection:
    def __init__(self):
        self.ranks = [Rank(rank_id + 1, *arguments) for rank_id, arguments in enumerate(description)]
        
    def __getitem__(self, index):
        return self.ranks[index]
    
rank_collection = RankCollection()

    
    