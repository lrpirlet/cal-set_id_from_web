
# Get and Set Id from Web

get_and_set_id_from_web is an optional utility to support any metadata plugin presenting two functions. The first is able to recreate the url of the metadata of a given book. The second is able to condensate the url into a unique id. Both function should be implemented into the metadata pluggin under the name : **id_from_url(self, url)** and **get_book_url(self, identifiers)**.

It present a customised internet browser from where to chose the book. This browser is running in the calibre environment and is a detached process from main calibre. One or several URL will be passed to main calibre who will update the database of the book. Later, the associated metadata plugin may be invoked to get the actual metadata.

It will also wipe out some fields that cannot be wiped out such as series... Maybe later this deletion will be optional.

# advantages

The search engine of some sites are misleading the pluggin. This should ensure that the id is, at least, correct.

The publicity pays some site, and this is measured by counters that react to interractive session only. This approach would provide some revenues at least for the search session that usually takes a few redirections.

The browser keeps cookies for the next sessions allowing easier access for a later access by calibre

The browser has a minimum bookmark capability, allowing direct access to the target site's search page.

One can use google search page instead of the target site's one.
