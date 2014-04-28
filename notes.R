a <- read.csv("~/chesschallenge/data/chessgames.csv")
a$whiteWins <- a$result == "1-0"
bound <- 2.5; a$s <- ifelse(a$totalScore < -bound, -bound, ifelse(a$totalScore > bound, bound, a$totalScore)); ## trim to [-bound,bound]

bin <- function(x,y,n=20)
{
    g <- cut(x, breaks=unique(quantile(x, prob=0:n/n, na.rm=TRUE)))
    x.mn <- tapply(x, g, mean, na.rm=TRUE);
    y.mn <- tapply(y, g, mean, na.rm=TRUE);
    list(x=x.mn, y=y.mn);
}

## simple linear model of whiteWins ~ s does pretty well
par(mfrow=c(1,2)); S <- c(0,1); plot(bin(a$s, a$whiteWins, n=100), type="o", ylim=S); grid(); summary(L <- lm(whiteWins ~ s, data=a, na.action=na.exclude)); plot(bin(predict(L), a$whiteWins, n=100), type="o", xlim=S, ylim=S); grid(); abline(a=0,b=1,col="grey",lty=3);




bin2 <- function(x,y,z,n=20)
{
    gx <- cut(x, breaks=unique(quantile(x, prob=0:n/n, na.rm=TRUE)))
    gy <- cut(y, breaks=unique(quantile(y, prob=0:n/n, na.rm=TRUE)))
    
    x.mn <- tapply(x, list(x=gx,y=gy), mean, na.rm=TRUE);
    y.mn <- tapply(y, list(x=gx,y=gy), mean, na.rm=TRUE);
    z.mn <- tapply(z, list(x=gx,y=gy), mean, na.rm=TRUE);
    list(x=x.mn, y=y.mn, z=z.mn);
}


z <- bin2(a$s, a$n, a$whiteWins);
matplot(z$z, type="o", lty=1, col=rainbow(ncol(z$z), end=4/6)); grid(); ## notice that score is pretty irrelevant at the beginning (maybe even hurts)


## linear model of whiteWins ~ s + s*n (or pctMidGame)
par(mfrow=c(2,2));
S <- c(0,1); plot(bin(a$s, a$whiteWins, n=100), type="o", ylim=S); grid();
summary(L <- lm(whiteWins ~ s                            , data=a, na.action=na.exclude)); plot(bin(predict(L), a$whiteWins, n=100), type="o", xlim=S, ylim=S); grid(); abline(a=0,b=1,col="grey",lty=3);
summary(L <- lm(whiteWins ~ s + s*n                      , data=a, na.action=na.exclude)); plot(bin(predict(L), a$whiteWins, n=100), type="o", xlim=S, ylim=S); grid(); abline(a=0,b=1,col="grey",lty=3);
summary(L <- lm(whiteWins ~ s + s*pctMidGame - pctMidGame, data=a, na.action=na.exclude)); plot(bin(predict(L), a$whiteWins, n=100), type="o", xlim=S, ylim=S); grid(); abline(a=0,b=1,col="grey",lty=3);
