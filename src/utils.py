def str_dist(s1, s2): # used to match kaggle team names to collected ones
    n1 = len(s1)
    n2 = len(s2)
    #s1 = s1.lower()
    #s2 = s2.lower()
    d = [[0 for x in range(n2)] for x in range(n1)]
    for i in range(min(n1, n2)):
        if s1[i] == s2[i]:
            d[i][i] = 30 * (i + 1)
        else:
            break
    for i in range(1, n1):
        for j in range(1, n2):
            d[i][j] = max(d[i][j], d[i - 1][j]) - 1
            d[i][j] = max(d[i][j], d[i][j - 1]) - 1
            if s1[i] == s2[j]:
                d[i][j] = max(d[i][j], d[i - 1][j - 1] + 25)
    return d[n1 - 1][n2 - 1]
