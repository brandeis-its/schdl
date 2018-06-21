angular.module('schdl.resetPasswd', [
  'ngStorage'
])

.controller('ResetPasswdCtrl', ['$scope', '$modalInstance', '$resource', 'School', function($scope, $modalInstance, $resource, School) {
  var ResetPasswd = $resource('/api/reset_password/:school');
  $scope.resetPasswd = function() {
    School.$promise.then(function() {
      ResetPasswd.save({
        school: School.fragment
      }, {
        email: $scope.resetPasswd.getEmail()
      }, function(response) {
        $scope.resetPasswd.success = true;
      }, function(response) {
        $scope.resetPasswd.failed = response.status;
      });
      $scope.resetPasswd.failed = null;
    });
  };
  $scope.resetPasswd.email = '';
  $scope.close = function() {
    $modalInstance.close();
  };
}])

;
