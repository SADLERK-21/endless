#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "EndlessCharacter.generated.h"

class UCameraComponent;
class USpotLightComponent;
class UInputAction;
class UInputMappingContext;
struct FInputActionValue;

UCLASS()
class ENDLESS_API AEndlessCharacter : public ACharacter
{
	GENERATED_BODY()

public:
	AEndlessCharacter();

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Endless")
	TObjectPtr<UCameraComponent> Camera;

	// Phone flashlight. Tune cone/intensity/color in a Blueprint child.
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Endless")
	TObjectPtr<USpotLightComponent> Flashlight;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Endless")
	float InteractDistance = 200.f;

	// Hook for click sound / battery logic in Blueprint.
	UFUNCTION(BlueprintImplementableEvent, Category = "Endless")
	void OnFlashlightToggled(bool bIsOn);

protected:
	virtual void SetupPlayerInputComponent(UInputComponent* PlayerInputComponent) override;

private:
	void Move(const FInputActionValue& Value);
	void Look(const FInputActionValue& Value);
	void Interact();
	void ToggleFlashlight();

	// shortcut: input is built in code (WASD/mouse/E/F), no rebinding; move to .uasset input when a settings menu is needed.
	UPROPERTY(Transient) TObjectPtr<UInputMappingContext> MappingContext;
	UPROPERTY(Transient) TObjectPtr<UInputAction> MoveAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> LookAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> InteractAction;
	UPROPERTY(Transient) TObjectPtr<UInputAction> FlashlightAction;
};
