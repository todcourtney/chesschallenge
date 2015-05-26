## matching engine
PYTHONPATH=common:ChessBoard python me/me.py data/www.chessgames.py.csv /tmp/pnl.csv 2>&1 | tee /tmp/log.txt

## gui
CHESS_GATEWAY=chl-login-jcs03 PYTHONPATH=ChessBoard:me:common python gui/gui.py

## strategies
#CHESS_GATEWAY=chl-login-jcs03 PATH=/jcs/users/mschubmehl/git/chesschallenge/stockfish-dd-src/src_c11:$PATH PYTHONPATH=common:ChessBoard python strat/examples.py BMM
while true; do CHESS_GATEWAY=chl-login-jcs03 PATH=/jcs/users/mschubmehl/git/chesschallenge/stockfish-dd-src/src_c11:$PATH PYTHONPATH=common:ChessBoard python strat/examples.py SCS SCO SCM SIMM M2M; sleep 1; done
