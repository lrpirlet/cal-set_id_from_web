## The issue

There are, at least, two different attitudes toward the program accessing a site to gather some information.

- Some sites just welcome "nice behaving" programs, sometime they even publish how the site could be accessed so that everybody does respect the others.
- Some sites just refuse non human access, treating any "BOT" as malware. Those sites usually do NOT publish the conditions for access, blocking the IP from where the bot is coming... (In a world where the IP address is dynamically allocated, this is impacting anyone who happens to use this IP adress...)

This is a choice I am not going to discuss, "chacun fait son lit comme il se couche", or rather : "Comme on fait son lit, on se couche !" (once you lie in bed, it's too late to make the bed...)

The consequence is that calibre is often blocked, usually at the search page.

My idea is to find the address of the metadata via an human driven internet browsers, then use this address to build the calibre id of the book and store it in calibre.

Once the id is known, using the metadata fill up, calibre is able to restore the URL and go immediately to the page to get the information.

This will reduce the number of access by calibre, this will fine tune when a site does present several edition of the same book (same ISBN).

Of course this suppose that the metadata fetcher does jumps directly to the page when the id is known.

This also implies that both get_book_url(self, identifiers) and id_from_url(self, URL) do exist in the metadata pluggin (see <https://www.mobileread.com/forums/showpost.php?p=4250552&postcount=13>).

## cal-set_id_from_web

In fact, the real name of this pluggin is ***get_and_set_id_manually_from_web***... a bit long... Sooo I shortened it to cal-set_id_from_web

cal-set_id_from_web is a calibre pluggin that can be installed in calibre. It present a customised internet browser from where to chose the volume by surfing from google to the page of the book. Note  this browser does NOT have any handling of malware... do be careful.

Once on the page, it will record the id, using the id_from_url() to find both the id_name and the id value.

Incidentally, cal-set_id_from_web is also able to wipe out some metadata fields that calibre will not touch if nothing replaces it. the field series is an example.

Once all that is set, the metadata source plugging may be invoked and because the id is (assumed to be) the prime hint, all the downloaded metadata will be accurate.
