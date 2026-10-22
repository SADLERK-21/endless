#include "EndlessCharacter.h"
#include "Endless.h"
#include "Interactable.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/PointLightComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputModifiers.h"

AEndlessCharacter::AEndlessCharacter()
{
	GetCapsuleComponent()->InitCapsuleSize(40.f, 90.f);
	GetCharacterMovement()->MaxWalkSpeed = 180.f; // slow walk: the player must have time to look

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(GetCapsuleComponent());
	Camera->SetRelativeLocation(FVector(0.f, 0.f, 64.f));
	Camera->bUsePawnControlRotation = true;

	DebugLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("DebugLight"));
	DebugLight->SetupAttachment(Camera);
	DebugLight->SetIntensityUnits(ELightUnits::Candelas);
	DebugLight->SetIntensity(150.f); // apartment lamps are 8 cd; this lights a whole room at the level's -3 EV exposure
	DebugLight->SetAttenuationRadius(3000.f);
	DebugLight->SetCastShadows(false); // no shadows: see into every corner
	DebugLight->SetVisibility(false);
}

void AEndlessCharacter::SetupPlayerInputComponent(UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	auto MakeAction = [this](EInputActionValueType Type)
	{
		UInputAction* Action = NewObject<UInputAction>(this);
		Action->ValueType = Type;
		return Action;
	};
	MoveAction = MakeAction(EInputActionValueType::Axis2D);
	LookAction = MakeAction(EInputActionValueType::Axis2D);
	InteractAction = MakeAction(EInputActionValueType::Boolean);

	MappingContext = NewObject<UInputMappingContext>(this);
	// D = +X, A = -X, W = +Y (swizzle), S = -Y (swizzle + negate)
	MappingContext->MapKey(MoveAction, EKeys::D);
	MappingContext->MapKey(MoveAction, EKeys::A).Modifiers.Add(NewObject<UInputModifierNegate>(MappingContext));
	MappingContext->MapKey(MoveAction, EKeys::W).Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(MappingContext));
	FEnhancedActionKeyMapping& Back = MappingContext->MapKey(MoveAction, EKeys::S);
	Back.Modifiers.Add(NewObject<UInputModifierSwizzleAxis>(MappingContext));
	Back.Modifiers.Add(NewObject<UInputModifierNegate>(MappingContext));

	UInputModifierNegate* InvertY = NewObject<UInputModifierNegate>(MappingContext);
	InvertY->bX = false;
	InvertY->bZ = false;
	MappingContext->MapKey(LookAction, EKeys::Mouse2D).Modifiers.Add(InvertY);

	MappingContext->MapKey(InteractAction, EKeys::E);
#if !UE_BUILD_SHIPPING
	DebugLightAction = MakeAction(EInputActionValueType::Boolean);
	MappingContext->MapKey(DebugLightAction, EKeys::F);
#endif

	if (APlayerController* PC = Cast<APlayerController>(GetController()))
	{
		if (UEnhancedInputLocalPlayerSubsystem* Subsystem = ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(PC->GetLocalPlayer()))
		{
			Subsystem->AddMappingContext(MappingContext, 0);
		}
	}

	UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!Input)
	{
		UE_LOG(LogEndless, Error, TEXT("EnhancedInputComponent missing - check Config/DefaultInput.ini"));
		return;
	}
	Input->BindAction(MoveAction, ETriggerEvent::Triggered, this, &AEndlessCharacter::Move);
	Input->BindAction(LookAction, ETriggerEvent::Triggered, this, &AEndlessCharacter::Look);
	Input->BindAction(InteractAction, ETriggerEvent::Started, this, &AEndlessCharacter::Interact);
#if !UE_BUILD_SHIPPING
	Input->BindAction(DebugLightAction, ETriggerEvent::Started, this, &AEndlessCharacter::ToggleDebugLight);
#endif
}

void AEndlessCharacter::Move(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	AddMovementInput(GetActorForwardVector(), Axis.Y);
	AddMovementInput(GetActorRightVector(), Axis.X);
}

void AEndlessCharacter::Look(const FInputActionValue& Value)
{
	const FVector2D Axis = Value.Get<FVector2D>();
	AddControllerYawInput(Axis.X);
	AddControllerPitchInput(Axis.Y);
}

void AEndlessCharacter::Interact()
{
	const FVector Start = Camera->GetComponentLocation();
	const FVector End = Start + Camera->GetForwardVector() * InteractDistance;
	FHitResult Hit;
	const FCollisionQueryParams Params(SCENE_QUERY_STAT(EndlessInteract), false, this);
	if (GetWorld()->LineTraceSingleByChannel(Hit, Start, End, ECC_Visibility, Params))
	{
		AActor* Target = Hit.GetActor();
		if (Target && Target->Implements<UInteractable>())
		{
			IInteractable::Execute_Interact(Target, this);
		}
	}
}

void AEndlessCharacter::ToggleDebugLight()
{
	DebugLight->ToggleVisibility();
}
