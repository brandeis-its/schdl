angular.module('schdl.login', [
  'ngStorage'
])

.controller('LoginCtrl', ['$scope', 'Session', '$localStorage', '$modalInstance', 'School', function($scope, Session, $localStorage, $modalInstance, School) {
  $scope.login = function() {
    School.$promise.then(function() {
      Session.save({
        school: School.fragment
      }, {
        email: $scope.login.getEmail(),
        password: $scope.login.getPassword()
      }, function(response) {
        $localStorage.user = response;
        $scope.close();
      }, function(response) {
        if (response.status == 403) {
          var data = angular.fromJson(response.data);
          if (!angular.isDefined(data.reason)) {
            $scope.login.failed = 403;
          } else {
            $scope.login.failed = data.reason;
          }
        } else {
          $scope.login.failed = response.status;
        }
      });
      $scope.login.failed = false;
      $scope.login.password = '';
    });
  };
  $scope.login.email = '';
  $scope.login.password = '';
  $scope.close = function() {
    $modalInstance.close();
  };
}])

;
