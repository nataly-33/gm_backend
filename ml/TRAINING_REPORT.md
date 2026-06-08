# Training Report — music_classifier.pkl

Dataset: ml/data/dataset_sintetico.csv (500k filas de muestra de 3M)

## Género
```
              precision    recall  f1-score   support

   classical       0.76      0.76      0.76      7157
     country       0.77      0.77      0.77      7244
      cumbia       0.77      0.78      0.77      7138
  electronic       0.78      0.77      0.77      7115
        folk       0.76      0.76      0.76      7173
     hip-hop       0.77      0.77      0.77      7210
        jazz       0.74      0.76      0.75      7152
        lofi       0.75      0.76      0.76      6975
         pop       0.77      0.77      0.77      7197
         r&b       0.73      0.77      0.75      7161
   reggaeton       0.81      0.77      0.79      7119
        rock       0.79      0.77      0.78      7259
       salsa       0.77      0.77      0.77      6989
      techno       0.78      0.77      0.77      7111

    accuracy                           0.77    100000
   macro avg       0.77      0.77      0.77    100000
weighted avg       0.77      0.77      0.77    100000

```

## Mood
```
              precision    recall  f1-score   support

       angry       0.78      0.78      0.78     12390
       chill       0.78      0.78      0.78     12515
   energetic       0.80      0.78      0.79     12498
       happy       0.79      0.79      0.79     12471
     hopeful       0.78      0.78      0.78     12391
   nostalgic       0.76      0.78      0.77     12547
    romantic       0.76      0.78      0.77     12537
         sad       0.80      0.78      0.79     12651

    accuracy                           0.78    100000
   macro avg       0.78      0.78      0.78    100000
weighted avg       0.78      0.78      0.78    100000

```

## Tempo
```
              precision    recall  f1-score   support

        fast       0.67      0.67      0.67     33169
      medium       0.67      0.67      0.67     33441
        slow       0.67      0.67      0.67     33390

    accuracy                           0.67    100000
   macro avg       0.67      0.67      0.67    100000
weighted avg       0.67      0.67      0.67    100000

```

