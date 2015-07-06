// Copyright (c) 2015, DataXu
// All rights reserved.

// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//     * Redistributions of source code must retain the above copyright
//       notice, this list of conditions and the following disclaimer.
//     * Redistributions in binary form must reproduce the above copyright
//       notice, this list of conditions and the following disclaimer in the
//       documentation and/or other materials provided with the distribution.
//     * Neither the name of the <organization> nor the
//       names of its contributors may be used to endorse or promote products
//       derived from this software without specific prior written permission.

// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
// ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
// WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
// DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY
// DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
// (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
// LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
// ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
// (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
// SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

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
