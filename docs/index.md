# Documentation

## General
* To access dark mode for the site, the browser used to connect to the site must have a "dark mode" option enabled.
* When excluding or filtering categories, special syntax must be used. Replace all spaces with underscores `_`, and remove all percent (`%`) signs.
* When requesting a game, only use the game's abbreviation (i.e the contents of the url when browsing the game on speedrun.com). Examples: `smo`, `oot`, `sm64`.
* URL Parameters (or query strings) are used for many of the requests on the site. More information on parameters is available [here](https://www.botify.com/learn/basics/what-are-url-parameters).

## Homepage
`Location: /`

The homepage is the easiest way to navigate the features on the site, although it does not contain all the features possible within the site itself. 

The primary focus point on the homepage is for making a request to the analyzer itself. The homepage contains all the features allowed by the analyzer, making it easy to create a request at will.

## Analyzer
`Location: /data/<games>`

`Allowed Parameters: startdate, enddate, parseother, t, minimal, rejects`

The analyzer is the tool that allows for the collection of verification statistics for any particular game or set of games. The verification statistics by default will contain the last 200 runs verified for the leaderboard. Adding the `startdate` or `enddate` parameters will allow the user to filter by particular dates for the analyzed runs and the average runs.


* `enddate` is not allowed to be passed without `startdate`.
* The filter is inclusive of the dates that are sent with the request.

The `t` option is available to quickly filter by a particular starting date based on the current date. The following options are listed below.

* `lastmonth` - Gets the date exactly 1 month ago.
* `lastday` - Gets the date exactly 1 day ago.
* `lastweek` - Gets the date exactly 1 week (7 days) ago.
* `thismonth` - Gets the date at the start of the month.
* `thisday` - Gets the current date.
* `thisweek` - Gets the date at the start of the week (Sunday).
* `thisweekmondaystart` - The same as `thisweek`, but considers Monday the start.

Average runs is calculated by converting the date into a number representing the date in a year, getting the range of all the dates, then dividing the total number of runs by that range. The value is rounded to 2 decimals.

The average runs verified looks at the date runs were verified in the provided timespan (or last 200 runs), while the average runs looks at the date runs were submitted in the provided timespan (or last 200 runs).

`parseother`, when set to `yes`, will display more information about runs verified by individuals that are not currently registered as verifiers on the speedrun.com page (by default these individuals will be grouped together as "Other"). This is useful if the verification team has just removed individuals from the leaderboard.

`minimal`, when set to `yes`, will remove certain information from the request that normally requires extra API calls. If the Speedrun.com API is running slowly, it may be worth enabling this. The information removed is the number of runs in the queue and the average runs per day statistic.

`rejects`, when set to `yes`, will gather information about rejected runs for the particular game. This information will be displayed separately on individual user tabs, but will be combined when shown in the chart.

## Analyzer Data
`Location: /data/<games>/json`

`Allowed Parameters: startdate, enddate, parseother, t, rejects`

The analyzer data page will return the data collected from the [analyzer page](#Analyzer) in json format.

## Verification Leaderboard
`Location: /leaderboard/<games>`

`Allowed Parameters: startdate, enddate, parseother, t, rejects`

The verification leaderboard will display a stylized leaderboard sorted by the amount of runs verified by individuals. The same rules for `startdate`, `enddate`, `parseother`, `t`, and `rejects` on the [analyzer page](#Analyzer) apply.

Credits to [Mark Eriksson](https://codepen.io/Markshall) for the base CSS.

### All-Time Verification Leaderboard
The verification leaderboard allows for the user to request a leaderboard of all-time verification statistics using SRC's own total verification statistic. 

To request this, simply set the `t` value to `alltime`.

A few things should be kept in mind when utilizing this unique leaderboard property:

- This request only supports one game at a time.
- The `parseother` parameter does not work with this request, meaning the user can only collect data on verifiers currently registered as verifiers on the leaderboard.
- The API endpoint utilized for these requests are deemed "unstable" by Speedrun.com, so they can change at a moment's notice. This site will (hopefully) remain up-to-date on any changes to this endpoint.
- The statistic calculated by Speedrun.com includes both verified and rejected runs, unlike all other requests on the site (which only deal with verified runs).

## Queue
`Location: /queue/<games>`

`Allowed Parameters: category, user, orderby, exclude, time`

The queue page will display a simple list of all the runs currently in the verification queue for any particular set of games. The games are separated by commas (for example: `smo,sm64`).

Clicking on the category text will allow the user to filter the current queue page by the category selected, and clicking on the runner's name will allow the user to filter the current queue page by the runner selected. These requests can also be done manually with the `category` and `user` parameters.

The `orderby` option allows the user to change the order of the runs in the verification queue. By default, the order goes by when the run is listed as completed in ascending order (oldest first). The available options to change the order are available in the [Speedrun.com API documentation](https://github.com/speedruncomorg/api/blob/master/version1/runs.md#get-runs).

The `exclude` option allows the user to exclude certain categories from the request.

The `time` option allows the user to filter runs by the time of the run. Examples: `?time=>7200` will return runs greater than 2:00:00, and `?time=<3600` will return times that are under 1:00:00.

## Records
`Location: /queue/<games>/records`

`Allowed Parameters: category, user, orderby, exclude, time`

The records page functions exactly like the [queue page](#Queue), but only returns the runs in the verification queue that are considered world records. This request does not work properly with categories that utilize more than 1 sub-category (such as [Ocarina of Time, Glitchless](http://speedrun.com/oot#Glitchless)).

## Verifier
`Location: /verifier/<examiner>`

`Allowed Parameters: game, exclude`

The verifier page will display a simple list of the last 200 runs verified by a user.

The `game` option allows the user to filter by a particular game on speedrun.com.

The `exclude` option allows the user to exclude certain categories from the request.