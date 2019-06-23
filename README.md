[![CircleCI](https://circleci.com/gh/pellepim/turoboro.svg?style=svg)](https://circleci.com/gh/pellepim/turoboro)
# turoboro
A python library for specifying recurring time rules and getting timestamps in return.

Typical usage would be to articulate the behaviour of recurring rules and to get exact points
in time where those rules ought to be executed.

I.e this library answers the following questions: 

Given a recurring rule,

1. when is the next time it happens?
2. when are all of the times it happens?
3. when are `n` times it happens?

Say for example you want to find out at what specific UTC time the rule "every thursday of every
third week of every second month at 8 o'clock UTC" would happen.

Ask turoboro! 

However, this is very much work in progress. So... basically don't use this library yet.