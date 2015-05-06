## matching engine
PYTHONPATH=common:$PYTHONPATH; python me/me.py <(shuf data/onelinegames/www.chessgames.com.csv) /tmp/pnl.csv
## pnl
export PYTHONPATH=common:$PYTHONPATH; watch python me/pnl.py /tmp/pnl.csv
## gui
while true; do PYTHONPATH=ChessBoard:common:me:$PYTHONPATH python gui/gui.py /tmp/pnl.csv; sleep 1; done

## strategies (python)
PATH=stockfish-dd-src/src:$PATH PYTHONPATH=me:ChessBoard:common:strat:$PYTHONPATH python strat/examples.py SCO SCS SCM SIMM M2M

## strategies (c++)
PATH=stockfish-dd-src/src:$PATH PYTHONPATH=me:ChessBoard:common:c++/swig:$PYTHOHNP python strat/run-cstrategy.py -s StockfishStrategy -i CSF
