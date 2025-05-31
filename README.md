# Gambling Bot

Interacting with the bot
The bot uses slash commands (e.g. /profile) and pinging with @Gambling Bot.

Each slash command shows the options you can pass to them, with some being required and some being optional.

How to play
To play with the bot, use any of the game commands (see the COMMANDS tab for the list)

Players start with 1,000 cash and level 0.

The bot uses a global economy so you can play in any server using the same profile.

Most (soon to be all) games support betting your hard earned cash, with an allin option to bet all your cash in the hopes to win big!

There's no level cap so you can play endlessly and nobody can be at the top of any leaderboard 'forever' (provided you don't hit the database cap... heh)

Play games, win cash, get to the top of the leaderboards!

Server and player perks can be purchased by donating to give you and/or your server an edge against the competition!

Every command in the bot has a help page. Call /help <name of command> (e.g. /help blackjack) to see the page, it will show any aliases that you can use when pinging with @Gambling Bot and some examples of how to use the command. You can also @Gambling Bot help blackjack

Note: the help is currently tailored for the @Gambling Bot ping variation as opposed to slash commands but there's no difference between either option so choose which you prefer. If you see any mentions of $someCommand just calling @Gambling Bot someCommand instead will work (e.g. @Gambling Bot replaced the old prefix of $ which is no longer supported)

Getting Started
# View your profile
/profile

# Flip a coin
/coinflip

# Play some blackjack
/blackjack

# Get free money
/work
/daily

# Get more free money and credit by voting
/vote

# Get _even more_ money and perks for making money faster
/donate

# Show the shop
/shop credit
/shop item

# Buy stuff
/buy boost
/buy item

# Show or activate your boosts
/boosts show
/boosts use
Getting started: Crypto Mine
The mine is a side-game added to keep you entertained in between game cooldowns or just to compete with friends.

# Start your crypto mine
/start_mine

# Dig in the mine every minute
/dig

# Craft some packs to buy units
/craft

# View the mine shop
/shop mine

# Buy units to expand your mine
/buy unit

# Upgrade your miners
/upgrade miner
Understanding the command help
To view all the available commands, you can call /help.

The help is linked to the COMMANDS tab on this website which is searchable and easier to use than /help

Commands look like this in the help:

@Gambling Bot commandName <bet> [hard]
@Gambling Bot commandName <bet> [<optionalBet>]
Arguments wrapped in [] are optional. Anything not wrapped in these must be passed in for the command to work.

Arguments wrapped in <> are where you can pass a value in, e.g. <bet> would be where you put 1000

In the case where you have [hard | h] this indicates an optional hard mode for the game with slightly increased difficulty in exchange for better odds.

Slash commands assist in this and tell you whether the argument is optional and, if it has a fixed number of choices, will present you with those choices (e.g. you will be able to choose Easy or Hard mode for the hard argument)

For example:

@Gambling Bot blackjack <bet> [hard | h]
You could call:

/blackjack 100
/blackjack 100 hard
/blackjack 100 h
In some cases, arguments are required as strings:

/coinFlip <heads|tails> <bet>
In this case, you can use:

/coinflip heads 100
/coinflip tails 100
Every command help page has examples that show the various different ways to use the command.

Bets and number arguments
All of the games in the bot support the same values for bets, as well as the shop and any other command that expects a number as an argument (like /craft).

You can bet using max (or m) to bet your Betting Maximum indicated by /me. You can also buy the maximum number of an item that you can afford, or sell the number of an item that you have using max or m as the count.

If you have less than your betting allowance, it will use all your current cash.

When betting, you can add the following letters after your bet as a shortcut for large numbers.

E.g. 1k = 1,000
y  = 1,000,000,000,000,000,000,000,000
z  = 1,000,000,000,000,000,000,000
e  = 1,000,000,000,000,000,000
p  = 1,000,000,000,000,000
t  = 1,000,000,000,000
g  = 1,000,000,000
m  = 1,000,000
k  = 1,000
All games and commands expect numbers as whole, positive numbers.

Fractional numbers will be rounded down.

Earning money
Cash Commands
The simplest way to earn money in the bot is via the various cash commands.

You can call /work to get some cash every 10 minutes, and /daily every day (resets at midnight regardless of when you called it)

Donators can get access to /overtime as well as /weekly, /monthly and /yearly.

You can see the commands you have access to as well as when they are ready on /cooldowns (/c)

Voting
If you don't mind watching a few ads, you can vote for the bot to get 100,000 x your player level.

Voting consecutively without a gap of more than 48 hours between votes will increase the multiplier.

Each 21st vote will be a 3x multipler, which stacks with your streak multipler.

Assuming you are level 1, the following cash reward table shows what you could receive by chaining votes:

Vote Number	Multipler	Reward
1-20	1x	100,000
21	3x	300,000
22 - 41	2x	200,000
42	6x	600,000
43 - 62	3x	300,000
63	9x	900,000
64 - 83	4x	400,000
84	12x	1,200,000
If you vote on all 3 links every 12 hours, you can get 21 votes every 3.5 days. Voting on all three links once per day will take a week.

At level one voting every 12h, you could earn 23,000,000, level 2 would be 46,000,000 and so on!

top.gg also offers double votes on weekends for bot votes (Friday - Sunday). As they offer double votes, the bot offers double rewards.

This means that if you voted for the bot using top.gg on the weekend for your 84th vote, you could get a 24x multiplier!

Time your top.gg bot votes on weekends and you can make a large amount of money reasonably quickly!

Lotto
A weekly lottery runs in the bot and is drawn at 11:00 Saturdays (London Time).

The starting value is 1,000,000 which is set immediately after the draw.

Every player can buy 1,000 tickets (each costing 1,000). Every ticket purchased increases the prize pot by 50,000

Buy tickets with /buy lotto X - As with all buy commands you can use max or a number to select the amount to buy.

When the draw is complete, the winner is posted in #lottery on the support server and sent a DM to tell them the winnings (you need the 'Allow direct messages from server members' enabled for this to work)

Earning XP
XP can be earned two ways:

Winning gambles
Earning Achievements
Each gamble win provides your winning cash, as well as an amount of XP. This differs for each game, although most currently give 100 per win.

You can see your current XP and player level with /profile

Achievements also exist to bolster your XP and are the fastest way to get it. There are achievements for gambling, earning cash and buying/finding items.

You can see your achievements with /profile achievements and item achievements with /profile achievements items

Each achievement has a current / target as well as a progress bar indicating your percentage to the target.

Every achievement earned grants 100xp. Generally these come in one at a time but when placing large bets with allIn it's common to get several achievements at once (e.g for cash earned).

Leaderboards
Gambling Bot has a leaderboard for everything. Gambling, items, mining, you name it there's a leaderboard.

See all the available leaderboards with /leaderboard

Show a leaderboard for your server with /leaderboard <id> (e.g /leaderboard blackjack). Use this to compete among friends in your server for the top spot!

Show a global leaderboard with /leaderboard <id> g (e.g. /leaderboard blackjack g). Global rankings is based on every player using the bot - compete for the coveted top spots!

Gambling
Now that you have some cash, what do you do with it?!

GAMBLE!!!

You can see the full list of gambles available in the bot with /help games.

The list shows the commands you can call to play the games, as well as aliases for the command.

Type the command and gamble away!

Game Guides
I promise I'll actually write these at some point 😬

## Multipliers

The bot uses multipliers to boost your rewards in certain scenarios:

- **Voting Streaks:** Consecutive votes increase your cash multiplier. Every 21st vote is a 3x multiplier, stacking with your streak.
- **Top.gg Double Votes:** Voting on weekends via top.gg gives double rewards (e.g., a 12x streak becomes 24x).
- **All-in Bets:** Some games offer higher multipliers when you use the all-in option.
- **Game Modes:** Hard mode in games like blackjack increases your payout multiplier.

Check `/help` for each command to see if multipliers apply.

## Games

The following games are available (see `/help games` for details):

- **Blackjack** (`/blackjack`)
- **Coinflip** (`/coinflip`)
- **Slots** (`/slots`)
- **Roulette** (`/roulette`)
- **Poker** (`/poker`)
- **Race** (`/race`)
- **Roll** (`/roll`)
- **Sevens** (`/sevens`)
- **Rock Paper Scissors** (`/rockpaperscissors`)
- **Find the Lady** (`/findthelady`)
- **Crypto Mine** (`/start_mine`, `/dig`, `/craft`)

Each game supports betting and most support multipliers for special modes or streaks.

## Console Focus (For Developers)

If you're running the bot locally and want to focus on the console output, use your terminal's "focus mode" or maximize the terminal window for easier debugging. All logs are also written to `bot.log` for review.
