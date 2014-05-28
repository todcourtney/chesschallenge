## matching engine
PYTHONPATH=common python me/me.py <(shuf data/onelinegames/www.chessgames.com.csv) /tmp/pnl.csv
## pnl
export PYTHONPATH=common; watch python me/pnl.py /tmp/pnl.csv
## gui
while true; do PYTHONPATH=ChessBoard:common:me python gui/gui.py /tmp/pnl.csv; sleep 1; done

## strategies (python)
PATH=/home/mschubmehl/code/chess/stockfish-dd-src/src_c11:$PATH PYTHONPATH=me:ChessBoard:common python strat/examples.py SCO SCS SCM SIMM M2M

## strategies (c++)
PATH=/home/mschubmehl/code/chess/stockfish-dd-src/src_c11:$PATH PYTHONPATH=me:ChessBoard:common:c++/swig python strat/run-cstrategy.py -s StockfishStrategy -i CSF
