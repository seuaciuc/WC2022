import streamlit as st
import numpy as np
import pandas as pd


### INPUTS
pklfile = 'WC2022.pkl'

## load data
scoreData = pd.read_pickle(pklfile)

##############################################################################
## GET RANKINGS
def getPoints(master,player):
    # identify NA entries
    flag = ~master['Team1score'].isna()
    # get scores
    master1 = master['Team1score'][flag]
    master2 = master['Team2score'][flag]
    player1 = player['Team1score'][flag]
    player2 = player['Team2score'][flag]
    # picks
    picks = sum(np.logical_and(master1==player1,master2==player2))
    # outcomes
    gt = np.logical_and(master1>master2,player1>player2)
    lt = np.logical_and(master1<master2,player1<player2)
    eq = np.logical_and(master1==master2,player1==player2)
    outcomes = sum(np.logical_or(np.logical_or(lt,gt),eq))
    # compute points
    points = outcomes + 2*picks
    return points, picks

# retrieve number of players
n = len(scoreData)-1 

# get player
Player = [scoreData[p]['Player'] for p in range(1,n+1)]

# initialize
Points = np.zeros(n).astype('int')
Picks = np.zeros(n).astype('int')

# loop over players
for p in range(0,n):
    Points[p], Picks[p] = getPoints(scoreData[0],scoreData[p+1])
    
# turn to data frame
rankings = pd.DataFrame([Player, Points, Picks]).T
# name columns
rankings.columns = ['Player','Points','Exact Picks']
# order it
rankings.sort_values(['Points','Exact Picks'],ascending=False,inplace=True,ignore_index=True)
# re-index to start at one
rankings.index = range(1,n+1)
##############################################################################

##############################################################################
## DISPLAY SCORES
@st.cache
def displayScores(scores):
    # convert dic to DF
    DF = pd.DataFrame(scores)
    # rearrange columns, only keep some
    DF = DF[['Date','Team1','Team1score','Team2score','Team2']]
    
    # add x column
    DF.insert(loc=3,column='x',value='x')
    # sort by date
    DF.sort_values(['Date'],ascending=True,inplace=True,ignore_index=True)
    return DF

##############################################################################
## SIDE BAR
st.sidebar.title("World Cup 2022")
options = ['Rankings','Scores']+Player
radio =  st.sidebar.radio(label='Show:',options=options,index=0)


##############################################################################
## RANKINGS
if radio == 'Rankings':
    st.table(rankings)

##############################################################################
## SCORES
else:
    # get index
    idx = np.where(np.array(options)==radio)[0][0]-1
    scores = displayScores(scoreData[idx])
    scores = scores.rename(columns={'Team1score':'S1','Team2score':'S2'})
    st.table(scores.style.format({'S1':'{:.0f}','S2':'{:.0f}','Date':'{:%b %d}'},na_rep=' '))
    