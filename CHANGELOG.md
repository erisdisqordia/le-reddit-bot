# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- Status visibility option (upstream only posted publicly)
- Ability to set custom text prefixes at the beginning of the fedi post, before author credit if enabled, and before the source URL if enabled
- Ability to search posts from `New`, `Top` or `Hot` or `Rising` etc, instead of only `New`
- Option to include or disable adding the post title as status text
- Option to include or disable credit to the original submitter
- Option to include or disable the source URL
- Option to replace URL links with an alternative such as libreddit or teddit for privacy
- Added example systemd service for management of the bot through systemctl
- Added CHANGELOG file
- Added option to send posts to Mastodon API schedule queue instead of posting, configurable with a delay option

### Fixed

- Fixed issue where some symbols in Reddit titles wouldn't be parsed correctly

### Changed

- Changed original bot behavior to reject all 18+ posts from Reddit
- Posts no longer automatically mark all images as NSFW on fedi
   - this was changed to an option to either match if the Reddit post is marked NSFW, to always force NSFW, or to never mark NSFW 

## [Upstream]

- No changelog kept