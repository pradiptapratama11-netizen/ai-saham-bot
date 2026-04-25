import yfinance as yf
import pandas as pd
from ta.trend import IchimokuIndicator
from sklearn.ensemble import RandomForestClassifier
import os

BOT_TOKEN=os.getenv("8104665909:AAFwSwb0V-XZKm_Fvpu1RIIURr0bquA-SYE")
CHAT_ID=os.getenv("6839765393")

stocks=pd.read_csv(
"saham_list.csv",
header=None
)[0].drop_duplicates().tolist()


################################
# Bluechip override
################################

quality_bluechips=[
"BBCA.JK",
"BBRI.JK",
"BMRI.JK",
"BBNI.JK",
"TLKM.JK"
]


def fundamental_score(stock):

    try:

        tk=yf.Ticker(stock)
        info=tk.info

        pbv=info.get("priceToBook")
        pe=info.get("trailingPE")
        roe=info.get("returnOnEquity")

        score=3

        if pbv and pbv<3:
            score+=2

        if pe and pe<22:
            score+=2

        if roe and roe>.12:
            score+=3

        return score

    except:
        return 3



def ai_score(df):

    try:

        d=df.copy()

        d["ret"]=d.Close.pct_change()
        d["ma20"]=d.Close.rolling(20).mean()
        d["ma50"]=d.Close.rolling(50).mean()

        d=d.dropna()

        if len(d)<100:
            return .5

        X=d[
        ["Close","Volume","ma20","ma50"]
        ]

        y=(d.ret.shift(-5)>0).astype(int)

        m=RandomForestClassifier(
            n_estimators=80
        )

        m.fit(
          X[:-1],
          y[:-1]
        )

        p=m.predict_proba(
          [X.iloc[-1]]
        )[0][1]

        return p

    except:
        return .5



strong=[]
watch=[]
avoid=[]


print(
"V6.5 BIAS FIX ENGINE..."
)


for s in stocks:

 try:

   df=yf.download(
      s,
      period="12mo",
      auto_adjust=True,
      progress=False
   )

   if len(df)<100:
      continue


   close=df.Close.squeeze()
   high=df.High.squeeze()
   low=df.Low.squeeze()
   vol=df.Volume.squeeze()

   alpha=0


   ###################
   # FUNDAMENTAL
   ###################

   alpha+=fundamental_score(s)



   ###################
   # ICHIMOKU
   ###################

   ichi=IchimokuIndicator(
      high,
      low
   )

   if close.iloc[-1] > ichi.ichimoku_base_line().iloc[-1]:
      alpha+=3



   ###################
   # RS
   ###################

   rs=(
      close.iloc[-1]/
      close.iloc[-60]
   )-1

   if rs>.05:
      alpha+=3



   ###################
   # ACCUMULATION
   ###################

   if vol.tail(5).mean() > vol.tail(20).mean():
      alpha+=3



   ###################
   # AI
   ###################

   prob=ai_score(df)

   alpha+=int(prob*6)



   conf=round(
      alpha*(1+prob),
      1
   )



   ###################
   # GRADE
   ###################

   if conf>25:
      grade="A+"

   elif conf>=22:
      grade="A"

   elif conf>=19:
      grade="B"

   else:
      grade="C"



   ###################
   # BIAS FIX CLASSIFY
   ###################

   if (
      prob<0.25
      and rs<0
      and s not in quality_bluechips
   ):

      avoid.append(
         (s,prob)
      )


   elif (
      s in quality_bluechips
      and conf>18
   ):

      watch.append(
         (
          s,
          conf,
          "QualityOverride"
         )
      )


   elif conf>=21:

      strong.append(
        (
         s,
         conf,
         grade
        )
      )


   else:

      watch.append(
        (
         s,
         conf,
         grade
        )
      )


 except:
   continue




strong=sorted(
strong,
key=lambda x:x[1],
reverse=True
)

watch=sorted(
watch,
key=lambda x:x[1],
reverse=True
)



print("\n🔥 STRONG BUY\n")

for x in strong[:10]:

 print(
   x[0],
   "| Conf",x[1],
   "|",x[2]
 )


print("\n👀 WATCHLIST\n")

for x in watch[:10]:

 print(
   x[0],
   "| Conf",x[1],
   "|",x[2]
 )


print("\n⚠ AVOID\n")

for x in avoid[:10]:

 print(
   x[0],
   "| Prob",
   round(x[1],2)
 )