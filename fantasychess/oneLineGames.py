import sys
import re
import os

def loadMovesAndResult(filenames):
    for filename in filenames:
        with open(filename, 'r') as f:
            for i, l in enumerate(f):
                l = l.strip()
                if l.startswith("[") or l == "":
                    lines = []
                    continue
                else:
                    src = "%s:%d" % (filename, i+1)
                    lines.append(l)

                    ## once we have result line, yield this game
                    if l.endswith("0-1") or l.endswith("1-0") or l.endswith("1/2-1/2"):
                        movesline = (" ".join(lines))
                        moves = re.sub("([0-9]+\\.) *", "\n\\1", movesline).lstrip()

                        moves = [m.strip().split(".") for m in moves.split("\n")]
                        n = len(moves)

                        turnNumbers = [int(m[0]) for m in moves]
                        assert turnNumbers == range(1,n+1)

                        moves = [m[1].split(" ") for m in moves]

                        assert len(moves[n-1]) in [2,3] ## black may not have moved, and result should be last
                        result = moves[n-1][-1]
                        assert result in ["1-0", "0-1", "1/2-1/2"]
                        moves[n-1] = moves[n-1][:-1]

                        assert all(len(m) in [1,2] for m in moves)

                        yield filename, i+1, moves, result


if __name__ == '__main__':
    filenames = sys.argv[1:]

    for filename, line, moves, result in loadMovesAndResult(filenames):
        filename = os.path.basename(filename)
        if filename.startswith("IB"):
            filename = filename[6]
        g = ",".join((filename, str(line), result," ".join(m for M in moves for m in M)))
        print g

