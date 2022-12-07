import streamlit as st
import numpy as np
import pandas as pd


### INPUTS
pklfile = 'WC2022.pkl'
firstPlayoffRow = 67 # first playoff row in excel file

## load data
scoreData = pd.read_pickle(pklfile)

##############################################################################
## GET RANKINGS
def getPoints(master,player,playoff=firstPlayoffRow-2):
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
    
    ### DEAL WITH PLAYOFF PENALTIES
    # get PK scores
    PK1master = master['PK1'][flag]
    PK2master = master['PK2'][flag]
    PK1player = player['PK1'][flag]
    PK2player = player['PK2'][flag]
    # only counts if 1) in playoffs (row>=playoff); 2) game ended in tie; 3) player predicted tie
    masterTie = master1==master2 # get entries with real ties
    playerTie = player1==player2 # get entries with player predicted ties
    PKflag = np.logical_and(masterTie,playerTie)
    PKflag = np.logical_and(PKflag, PKflag.keys()>=playoff) # now PKflag contains the rows where PK need to be assessed
    idx = PKflag.keys()[np.where(PKflag)[0]]
    # now loop over the indices above (remember to get .keys()[idx])
    PKextra = 0
    PKpicks = 0
    for row in idx:
        PKexact = PK1master[row]==PK1player[row] and PK2master[row]==PK2player[row]
        PKgt = PK1master[row]>PK2master[row] and PK1player[row]>PK2player[row]
        PKlt = PK1master[row]<PK2master[row] and PK1player[row]<PK2player[row]
        PKeq = PK1master[row]==PK2master[row] and PK1player[row]==PK2player[row]
        PKextra = PKextra + 2*PKexact + (PKgt or PKlt or PKeq)
        PKpicks = PKpicks + PKexact
   
    return points+PKextra, picks+PKpicks

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
def displayScores(scores,playoff=firstPlayoffRow-2):
    # convert dic to DF
    df = pd.DataFrame(scores)
    # rearrange columns, only keep some
    DF = df[['Date','Team1','Team1score','Team2score','Team2']]
    
    # get playoff entries with ties
    team1score = df['Team1score']
    team2score = df['Team2score']
    tie = team1score==team2score # get entries with real ties
    PKflag = np.logical_and(tie, DF.index>=playoff) # now PKflag contains the rows where PK need to be assessed
    idx = PKflag.keys()[np.where(PKflag)[0]]
    # insert penalty scores
    for row in idx:
        DF['Team1score'][row] = str(int(df['Team1score'][row])) + ' (' + str(int(df['PK1'][row])) +')'
        DF['Team2score'][row] = str(int(df['Team2score'][row])) + ' (' + str(int(df['PK2'][row])) +')'
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
    #st.table(scores.style.format({'S1':'{:.0f}','S2':'{:.0f}','Date':'{:%b %d}'},na_rep=' '))
    st.table(scores,na_rep=' ')
    