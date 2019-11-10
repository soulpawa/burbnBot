
# BurbnBot  
  
Instagram didn't start out as Instagram. It started out as … Burbn.   
  
## Getting Started  
  
BurbnBot help you automate some tasks on a popular social imaging network.  
### Prerequisites  
  
For this adventure you will need:  
* Python 3  
* Android Virtual Device (AVD) 
* Appium
  
### Installing  
  
The easy way
  
First, the Appium server
  
``` 
npm install -g appium
```  
  
more information [here](http://appium.io/docs/en/about-appium/getting-started/?lang=en#installing-appium).
  
The easy way to install the AVD is installing the Android Studio (I'll check a better way soon)

### A little example  

```python    
from BurbnBot.BurbnBot import BurbnBot
burbn = BurbnBot()
#will like 20 posts
burbn.interact_by_hashtagd(amount=20, hashtag="pizzanight")
#unfollow 20 users
burbn.unfollow_non_followers(avoid_saved=True, n_to_unfollows=20)
burbn.do_actions()
```


