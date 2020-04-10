# distance-checker

Most of the variables here are hard-coded, as this is essentially a proof of concept. To add destinations, create a file called "addresses.csv" with the columns "name" and "coords". The name should be the name of the destination, the coords should be the coordinates, address, or landmark you are navigating to.  The variable 'origin' in the file is what you should change to be the address whose distance you are checking everything against. 

You'll need a Google API key with access to the Places, Geocoding, and Directions APIs. Luckily Google gives $300 in monthly credit that will more than easily absorb the meager cost of these APIs. 

Right now it has set times of the day that it cycles through to check these addresses. The next step would be to modify this so that you would be able to specify in the data file what times you want to check arriving at or returning from these destinations. My ultimate plan is to hook this up to a webapp or some sort of exe so someone can enter in the relevent information and hit go, but I don't know how to do either of those things.
