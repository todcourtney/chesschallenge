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




## simple lag-by-src
L <- c(NA, 1:(nrow(a)-1)); L[which(a$src != a$src[L])] <- NA;
a$sL1 <- a$s[L]

## adding one lag of score helps to solve bouncing-around problems, bumps R2 12%->15%
par(mfrow=c(2,2));
S <- c(0,1); summary(L <- lm(whiteWins ~ s      , data=a, na.action=na.exclude)); plot(bin(predict(L), a$whiteWins, n=100), type="o", xlim=S, ylim=S); grid(); abline(a=0,b=1,col="grey",lty=3);
S <- c(0,1); summary(L <- lm(whiteWins ~ s + sL1, data=a, na.action=na.exclude)); plot(bin(predict(L), a$whiteWins, n=100), type="o", xlim=S, ylim=S); grid(); abline(a=0,b=1,col="grey",lty=3);





## best all-in model so far
S <- c(0,1); summary(L <- lm(whiteWins ~ s + sL1 + s*pctMidGame - pctMidGame, data=a, na.action=na.exclude)); plot(bin(predict(L), a$whiteWins, n=100), type="o", xlim=S, ylim=S); grid(); abline(a=0,b=1,col="grey",lty=3);

## Call:
## lm(formula = whiteWins ~ s + sL1 + s * pctMidGame - pctMidGame, 
##     data = a, na.action = na.exclude)
## 
## Residuals:
##      Min       1Q   Median       3Q      Max 
## -0.94734 -0.44596 -0.01334  0.46900  1.07382 
## 
## Coefficients:
##                 Estimate  Std. Error t value Pr(>|t|)    
## (Intercept)   0.43676265  0.00127895  341.50   <2e-16 ***
## s             0.14391660  0.00178097   80.81   <2e-16 ***
## sL1           0.06031617  0.00121081   49.81   <2e-16 ***
## s:pctMidGame -0.00114424  0.00002351  -48.68   <2e-16 ***
## ---
## 
## Residual standard error: 0.4569 on 135845 degrees of freedom
##   (1841 observations deleted due to missingness)
## Multiple R-squared:  0.1615,	Adjusted R-squared:  0.1615 
## F-statistic:  8721 on 3 and 135845 DF,  p-value: < 2.2e-16






## investigate use of openings
for(N in 1:4) {
    openings <- tapply(a$move, a$src, function(x) {paste(head(x,N), collapse=" ")});
    results <- a$result[match(names(openings), a$src)];
    z <- table(openings, results); z <- addmargins(head(z[order(-rowSums(z)),],10)); print(cbind(z, whiteWinFrac=round(z[,"1-0"]/z[,"Sum"],2)))
}


## look at success rate of various openings
history <- split(a$move, a$src)
a$history <- sapply(1:nrow(a), function(i) {if(i %% 10000 == 0) cat(i, "\n"); src <- a$src[i]; n <- a$n[i]; paste(history[[src]][1:n], collapse=" ")})
winPct <- tapply(a$whiteWins, a$history, function(x) {ifelse(length(x) > 100, mean(x), NA)});
winPct <- winPct[which(!is.na(winPct))];
t(t(winPct))

## for export to python
cat(paste("{", paste(sprintf("'%s':%f", names(winPct), winPct), collapse=", "), "}", sep=""), "\n")
## prettier
cat("{\n"); n <- names(winPct); for(i in 1:length(winPct)) {if(i > 1 && substr(n[i], 1, nchar(n[i-1])) != n[i-1]) cat("\n"); cat(sprintf(", '%s':%f", n[i], winPct[i]));}; cat("\n}\n")

a$openingWinPct <- winPct[match(a$history, names(winPct))]


## blending this lookup table with existing model








a <- do.call("rbind", lapply(Sys.glob("~/chesschallenge/data/*.csv"), function(f) {cat(f, "\n"); read.csv(f, nrows=300000)}))
