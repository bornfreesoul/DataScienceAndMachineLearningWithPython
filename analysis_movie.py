#!/usr/bin/env python

import operator
import pandas
import numpy
import scipy.spatial

def ComputeDistance(a, b):
    genresA = a[1]
    genresB = b[1]
    genreDistance = scipy.spatial.distance.cosine(genresA, genresB)
    popularityA = a[2]
    popularityB = b[2]
    popularityDistance = abs(popularityA - popularityB)
    return genreDistance + popularityDistance

def getNeighbors(movieID, K):
    distances = []
    for movie in movieDict:
        if (movie != movieID):
            dist = ComputeDistance(movieDict[movieID], movieDict[movie])
            distances.append((movie, dist))
    distances.sort(key=operator.itemgetter(1))
    neighbors = []
    for x in range(K):
        neighbors.append(distances[x][0])
    return neighbors

print "\nRatings:"
r_cols = ['user_id', 'movie_id', 'rating']
ratings = pandas.read_csv('./data/movielens/u.data', sep='\t', names=r_cols, usecols=range(3))
print ratings.head()

print "\nMovies:"
m_cols = ['movie_id', 'title']
movies = pandas.read_csv('./data/movielens/u.item', sep='|', names=m_cols, usecols=range(2))
print movies.head()

print "\nMovie Ratings Merged:"
ratings = pandas.merge(movies, ratings)
print "Movie Ratings Merged:"
print ratings.head()

print "\nMovie Ratings:"
movieRatings = ratings.pivot_table(index=['user_id'],columns=['title'],values='rating')
print movieRatings.head()

print "\nUser Ratings:"
userRatings = ratings.pivot_table(index=['user_id'],columns=['title'],values='rating')
print userRatings.head()

print "\nUser Ratings Correlation:"
corrMatrix = userRatings.corr()
print corrMatrix.head()

print "\nUser Ratings Correlation with min 100 ratings:"
corrMatrix = userRatings.corr(method='pearson', min_periods=100)
corrMatrix.head()

print "\nMovies I have watched & rated"
myRatings = userRatings.loc[0].dropna()
print myRatings

print "\nBuilding Similarities..."
simCandidates = pandas.Series()
for i in range(0, len(myRatings.index)):
    print "Adding Similarities for " + myRatings.index[i] + "..."
    # Retrieve similar movies to this one that I rated
    sims = corrMatrix[myRatings.index[i]].dropna()
    # Now scale its similarity by how well I rated this movie
    sims = sims.map(lambda x: x * myRatings[i])
    # Add the score to the list of similarity candidates
    simCandidates = simCandidates.append(sims)

print "\nStar Wars (1977) Ratings:"
starWarsRatings = movieRatings['Star Wars (1977)']
print starWarsRatings.head(10)

print "\nMovie Ratings Correalted with Star Wars"
similarMovies = movieRatings.corrwith(starWarsRatings)
similarMovies = similarMovies.dropna()
df = pandas.DataFrame(similarMovies)
print df.head(10)

print "\nMovies sorted by correlation to Star Wars"
print similarMovies.sort_values(ascending=False)[:20]

print "\nExploratory data by no of ratings and mean rating"
movieStats = ratings.groupby('title').agg({'rating': [numpy.size, numpy.mean]})
print movieStats.head()

print "\nRemoved Movies with less than 100 ratings"
popularMovies = movieStats['rating']['size'] >= 100
print movieStats[popularMovies].sort_values([('rating', 'mean')], ascending=False)[:15]

print "\nJoining data with the original set of similar movies to Star Wars"
df = movieStats[popularMovies].join(pandas.DataFrame(similarMovies, columns=['similarity']))
print df.head()

print "\nMovies sorted by correlation to Star Wars"
print df.sort_values(['similarity'], ascending=False)[:15]

print "\nExploratory Sorted Movie Recommendations based on my ratings:"
simCandidates.sort_values(inplace = True, ascending = False)
print simCandidates.head(10)

print "\nRemoving Duplicates..."
simCandidates = simCandidates.groupby(simCandidates.index).sum()
simCandidates.sort_values(inplace = True, ascending = False)
print simCandidates.head(10)

print "\nRemoving Movies I have already watched & rated..."
filteredSims = simCandidates.drop(myRatings.index)
print filteredSims.head(10)

print "\nGrouping by total and average ratings :"
movieProperties = ratings.groupby('movie_id').agg({'rating': [numpy.size, numpy.mean]})
print movieProperties.head()

print "\nNormalising..."
movieNumRatings = pandas.DataFrame(movieProperties['rating']['size'])
movieNormalizedNumRatings = movieNumRatings.apply(lambda x: (x - numpy.min(x)) / (numpy.max(x) - numpy.min(x)))
print movieNormalizedNumRatings.head()

print "\nGetting genre info.."
movieDict = {}
with open(r'./data/movielens/u.item') as f:
    temp = ''
    for line in f:
        fields = line.rstrip('\n').split('|')
        movieID = int(fields[0]) 
        name = fields[1]
        genres = fields[5:25]
        genres = map(int, genres)
        movieDict[movieID] = (name, genres, movieNormalizedNumRatings.loc[movieID].get('size'), movieProperties.loc[movieID].rating.get('mean'))
print "Sample Data ", movieDict[1]
print "Sample Data ", movieDict[2]
print "Sample Data ", movieDict[3]
print "Sample Data ", movieDict[4]
print "\nDistance b/w movie %s & %s is %s\n" %(movieDict[2][0], movieDict[4][0], ComputeDistance(movieDict[2], movieDict[4]))
K = 10
avgRating = 0
neighbors = getNeighbors(1, K)
for neighbor in neighbors:
    avgRating += movieDict[neighbor][3]
    print movieDict[neighbor][0] + " " + str(movieDict[neighbor][3])
    avgRating /= float(K)
print "\nAvg rating for %s nearest neighbours to %s is %s\n" %(K, movieDict[1][0], avgRating)
