angular.module('schdl.verify', ['ngResource'])

.factory('Verify', ['$resource', function($resource) {
  return $resource('/api/verify/:school');
}])

.controller('VerifyCtrl', ['$scope', 'School', 'titleService', 'results', 'Verify', '$location', function($scope, School, titleService, results, Verify, $location) {
  $scope.type = results.type;
  $scope.status = results.status;
  // If a new email address was just added to the account, reload user data to get it
  if (results.type == 'add_email' && results.status == 'success') {
    $scope.get_user_data();
  }
  titleService('Email Verification');
  $scope.doResetPasswd = function() {
    if ($scope.doResetPasswd.password !== $scope.doResetPasswd.password2) {
      $scope.doResetPasswd.failure = 'nomatch';
    } else if ($scope.doResetPasswd.password === '') {
      $scope.doResetPasswd.failure = 'blank';
    } else {
      results = Verify.save({
        school: School.fragment
      }, {
        secret: $location.search().secret,
        password: $scope.doResetPasswd.password
      }, function() {
        $scope.type = results.type;
        $scope.status = results.status;
      });
      $scope.doResetPasswd.failure = null;
      $scope.doResetPasswd.password = '';
      $scope.doResetPasswd.password2 = '';
    }
  };
  $scope.doResetPasswd.failure = null;
  $scope.doResetPasswd.password = '';
  $scope.doResetPasswd.password2 = '';
}])

;
