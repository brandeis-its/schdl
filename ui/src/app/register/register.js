angular.module('schdl.register', [
  'ngStorage'
])

.controller('RegisterCtrl', ['$scope', '$localStorage', '$modalInstance', 'School', 'User', function($scope, $localStorage, $modalInstance, School, User) {
  $scope.register = function() {
    var first = $scope.register.getFirst();
    var last = $scope.register.getLast();
    var email = $scope.register.getEmail();
    var password = $scope.register.getPassword();
    var password2 = $scope.register.getPassword2();
    if (password !== password2) {
      $scope.register.failed = 'passmatch';
      return;
    } else if (!password) {
      $scope.register.failed = 'nopassword';
      return;
    } else if (!email) {
      $scope.register.failed = 'noemail';
      return;
    } else if (!first && !last) {
      $scope.register.failed = 'noname';
      return;
    }
    School.$promise.then(function() {
      User.save({
        'school': School.fragment
      }, {
        'first': first,
        'last': last,
        'email': email,
        'password': password
      }, function(response) {
        $scope.register.success = true;
      }, function(response) {
        $scope.register.failed = response.status;
      });
    });
    $scope.register.failed = false;
  };
  $scope.close = function() {
    $modalInstance.close();
  };
  $scope.register.failed = false;
  $scope.register.first = '';
  $scope.register.last = '';
  $scope.register.email = '';
  $scope.register.password = '';
  $scope.register.password2 = '';
}])

;
