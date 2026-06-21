# Yongyi v5
import json
from datetime import datetime

class KE:
    GROUPS=["产品词","场景词","竞品词"]
    @staticmethod
    def get_kws():
        return [{"w":"环氧磨石","g":"产品词","v":5800},{"w":"无机磨石","g":"产品词","v":4200},{"w":"医院地坪","g":"场景词","v":3200}]
    @staticmethod
    def gen_video(kw,grp):
        return {"kw":kw,"hook":"15年师傅说"+kw,"tags":"#永颐金磨石"}

class CA:
    @staticmethod
    def get_comps():
        return [{"n":"A","f":"3/wk"},{"n":"B","f":"1/wk"}]
    @staticmethod
    def surpass(c):
        return {"adv":"14x","acts":["daily"]}

if __name__=="__main__":
    print(f"Kws:{len(KE.get_kws())}")
    print("Ready")
