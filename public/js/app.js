var webhooks = angular.module('webhooks', []);

webhooks.filter('fromNow', function() {
  return function(date) {
    return moment(date).fromNow(true);
  }
});

webhooks.filter('short_hash', function(){
  return function(hash){
    if (hash) {
      return hash.substring(0, 8);
    } else {
      return 'No Hash';
    }
  }
});

webhooks.controller('WebhooksControl', function($scope, $http){
  $scope.app_data = {};
  $scope.active_requests = 0;
  $scope.search_data = {};
  $scope.data = function(){
    return $scope.app_data;
  };

  $scope.update_data = function(){
    $scope.active_requests += 1;
    $http.get('/data').success(function(data) {
      $scope.active_requests -= 1;
      console.log(data)
      $scope.app_data = data;
    });
  };

  $scope.search = function(){
    $scope.active_requests += 1;
    $http.post('/search', $scope.search_data).success(function(data) {
      console.log(data)
      $scope.active_requests -= 1;
      $scope.app_data.events = data.results
    });
  };

});
