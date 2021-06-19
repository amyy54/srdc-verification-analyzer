# Documentation

## General
* To access dark mode for the site, the browser used to connect to the site must have a "dark mode" option enabled.
* When excluding or filtering categories, special syntax must be used. Replace all spaces with underscores `_`, and remove all percent (`%`) signs.
* When requesting a game, only use the game's abbreviation (i.e the contents of the url when browsing the game on speedrun.com). Examples: `smo`, `oot`, `sm64`.

## Homepage
`Location: /`

The homepage is the easiest way to navigate the features on the site, although it does not contain all the features possible within the site itself. 

The primary focus point on the homepage is for making a request to the analyzer itself. The homepage contains all the features allowed by the analyzer, making it easy to create a request at will.

## Analyzer
`Location: /data/<game>`

`Allowed Parameters: startdate, enddate, parseother`

The analyzer is the tool that allows for the collection of verification statistics for any particular game. The verification statistics by default will contain the last 200 runs verified for the leaderboard. Adding the `startdate` or `enddate` parameters will allow the user to filter by particular dates for the analyzed runs and the average runs.

* `enddate` is not allowed to be passed without `startdate`.
* The filter is inclusive of the dates that are sent with the request.

Average runs is calculated by converting the date into a number representing the date in a year, getting the range of all the dates, then dividing the total number of runs by that range. The value is rounded to 2 decimals.

The average runs verified looks at the date runs were verified in the provided timespan (or last 200 runs), while the average runs looks at the date runs were submitted in the provided timespan (or last 200 runs).

`parseother`, when set to `yes`, will display more information about runs verified by individuals that are not currently registered as verifiers on the speedrun.com page (by default these individuals will be grouped together as "other"). This is useful if the verification team has just removed individuals from the leaderboard.

## Queue
`Location: /queue/<games>`

`Allowed Parameters: category, user, orderby, exclude`

The queue page will display a simple list of all the runs currently in the verification queue for any particular set of games. The games are separated by commas (for example: `smo,sm64`).

Clicking on the category text will allow the user to filter the current queue page by the category selected, and clicking on the runner's name will allow the user to filter the current queue page by the runner selected. These requests can also be done manually with the `category` and `user` parameters.

The `orderby` option allows the user to change the order of the runs in the verification queue. By default, the order goes by the runs submitted in ascending order (oldest first). The available options to change the order are available in the [Speedrun.com API documentation](https://github.com/speedruncomorg/api/blob/master/version1/runs.md#get-runs).

The `exclude` option allows the user to exclude certain categories from the request.

## Records
`Location: /queue/<games>/records`

`Allowed Parameters: category, user, orderby, exclude`

The records page functions exactly like the [queue page](#Queue), but only returns the runs in the verification queue that are considered world records. This request does not work properly with categories that utilize more than 1 sub-category (such as [Ocarina of Time, Glitchless](http://speedrun.com/oot#Glitchless)).

## Verifier
`Location: /verifier/<examiner>`

`Allowed Parameters: game, exclude`

The verifier page will display a simple list of the last 200 runs verified by a user.

The `game` option allows the user to filter by a particular game on speedrun.com.

The `exclude` option allows the user to exclude certain categories from the request.