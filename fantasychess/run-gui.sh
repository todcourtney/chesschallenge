## gui
while true; do PYTHONPATH=ChessBoard:common:me:$PYTHONPATH:/usr/lib64/python2.7/site-packages python gui/gui.py /tmp/pnl.csv; sleep 1; done
