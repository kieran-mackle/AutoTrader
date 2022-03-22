# Market Scanning With AutoTrader

Not ready to give an algorithm complete control over your trading, but still want to 
have something automatically scan the market for you? AutoTrader can help. Using 
[scan mode](autotrader-scan-config) in AutoTrader is effortless, and you will recieve
email updates whenever your strategy gets a hit, similar to the one shown below.


> Dear <your name here>,
>
> This is an automated message to notify you of a recent match in a market scan 
> you are running. The details of the scan are as follows.
>
> Time of scan: 12:32:23.
>
> Scan strategy: SuperTrend.
>
> Scan index: major.
>
> The results from the scan are shown in the table below.
> 
> | Pair | Signal Price | Size | Stop Loss | Take Profit |
> | ----- | ------- | ---- | ---- | --- |
> | EURUSD=X | 1.17426  | Short | None | None |
>
>
> All the best in your trading endeavours,
>
> AutoTrader


```{seealso}
See this [blog post](https://kieran-mackle.github.io/AutoTrader/2021/09/27/developing-scanner.html)
for a detailed walkthrough developing a trend-detecting market scanner.
```